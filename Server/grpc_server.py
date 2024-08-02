from concurrent import futures
import grpc
import item_pb2
import item_pb2_grpc
from models import SessionLocal, Product, Manufacturer, Category, Review
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from sqlalchemy import asc, desc, and_, or_, not_, select, exists
from sqlalchemy.orm import aliased, Session, joinedload
from grpc_reflection.v1alpha import reflection
import os
import logging
from google.protobuf import message
from google.protobuf.internal import containers

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure DATABASE_URL is set
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set correctly")
logger.info(f"DATABASE_URL: {DATABASE_URL}")

class ProductService(item_pb2_grpc.ProductServiceServicer):
    def GetProduct(self, request, context):
        logger.info(f"Received GetProduct request: {request}")
        db: Session = SessionLocal()
        try:
            db_product = db.query(Product).options(
                joinedload(Product.manufacturer),
                joinedload(Product.category),
                joinedload(Product.reviews)
            ).filter(Product.id == UUID(request.id)).first()
            
            if db_product is None:
                logger.warning("Product not found")
                context.abort(grpc.StatusCode.NOT_FOUND, "Product not found")

            response = self.product_to_response(db_product)

            if request.field_mask.paths:
                self.mask_response(response, request.field_mask)

            logger.info("GetProduct request processed successfully")
            return response
        except Exception as e:
            logger.error(f"Error processing GetProduct request: {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Internal server error: {str(e)}")
        finally:
            db.close()

    def ListProducts(self, request, context):
        logger.info(f"Received ListProducts request: {request}")
        db: Session = SessionLocal()
        try:
            query = db.query(Product).options(
                joinedload(Product.manufacturer),
                joinedload(Product.category),
                joinedload(Product.reviews)
            )

            # Apply filtering if any
            if request.base_request.filter:
                filter_condition = self.apply_filter(query, request.base_request.filter)
                query = query.filter(filter_condition)
            
            # Apply ordering if any
            for order_by in request.base_request.order_by:
                query = self.apply_order_by(query, order_by)

            # Apply pagination
            pagination = request.base_request.pagination
            if pagination:
                query = query.offset(pagination.skip).limit(pagination.limit)

            db_products = query.all()
            logger.debug(f"Number of products found: {len(db_products)}")

            response = item_pb2.ProductListResponse()
            for db_product in db_products:
                product_response = self.product_to_response(db_product)
                
                # Apply nested filters
                if request.nested_filters.HasField('review_filter'):
                    self.apply_nested_filter(product_response.reviews, request.nested_filters.review_filter)
                
                if request.base_request.field_mask.paths:
                    self.mask_response(product_response, request.base_request.field_mask)
                
                response.products.append(product_response)

            logger.info(f"ListProducts request processed successfully. Returning {len(response.products)} products.")
            return response
        except Exception as e:
            logger.error(f"Error processing ListProducts request: {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Internal server error: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def product_to_response(db_product):
        response = item_pb2.ProductResponse(
            id=str(db_product.id),
            name=db_product.name,
            description=db_product.description,
            price=db_product.price,
            manufacturer_id=str(db_product.manufacturer_id),
            category_id=str(db_product.category_id),
            image=db_product.image,
            country_of_origin=db_product.country_of_origin,
            created_at=str(db_product.created_at),
            updated_at=str(db_product.updated_at)
        )

        if db_product.manufacturer:
            response.manufacturer.id = str(db_product.manufacturer.id)
            response.manufacturer.name = db_product.manufacturer.name

        if db_product.category:
            response.category.id = str(db_product.category.id)
            response.category.name = db_product.category.name

        for review in db_product.reviews:
            review_response = response.reviews.add()
            review_response.id = str(review.id)
            review_response.product_id = str(review.product_id)
            review_response.user_id = str(review.user_id)
            review_response.rating = review.rating
            review_response.text = review.text
            review_response.is_visible = review.is_visible
            review_response.created_at = str(review.created_at)
            review_response.updated_at = str(review.updated_at)

        return response

    @staticmethod
    def apply_filter(query, filter):
        condition = filter.WhichOneof('condition')
        logger.debug(f"Applying filter condition: {condition}")

        if condition == 'and':
            and_filter = getattr(filter, 'and')
            and_filters = [ProductService.apply_filter(query, subfilter) for subfilter in and_filter.filters]
            return and_(*and_filters)
        elif condition == 'or':
            or_filter = getattr(filter, 'or')
            or_filters = [ProductService.apply_filter(query, subfilter) for subfilter in or_filter.filters]
            return or_(*or_filters)
        elif condition == 'not':
            not_filter = getattr(filter, 'not')
            return not_(ProductService.apply_filter(query, not_filter.filter))
        elif condition == 'field':
            return ProductService.apply_field_filter(filter.field)
        else:
            logger.warning(f"Unknown filter condition: {condition}")
            return True

    @staticmethod
    def apply_field_filter(field_filter):
        field_path = field_filter.field.split('.')
        if len(field_path) > 1:
            # Nested field
            related_model = getattr(Product, field_path[0]).property.mapper.class_
            related_alias = aliased(related_model)
            return exists().where(
                and_(
                    getattr(Product, f"{field_path[0]}_id") == related_alias.id,
                    ProductService.get_field_filter(related_alias, field_path[1], field_filter)
                )
            )
        else:
            return ProductService.get_field_filter(Product, field_filter.field, field_filter)

    @staticmethod
    def get_field_filter(model, field, field_filter):
        operation = field_filter.WhichOneof('operation')
        if operation == 'string_op':
            string_op = field_filter.string_op
            if string_op.HasField('eq'):
                return getattr(model, field) == string_op.eq
            elif string_op.HasField('like'):
                return getattr(model, field).like(f"%{string_op.like}%")
        elif operation == 'int_op':
            int_op = field_filter.int_op
            if int_op.HasField('eq'):
                return getattr(model, field) == int_op.eq
            elif int_op.HasField('lt'):
                return getattr(model, field) < int_op.lt
            elif int_op.HasField('gt'):
                return getattr(model, field) > int_op.gt
        elif operation == 'timestamp_op':
            timestamp_op = field_filter.timestamp_op
            if timestamp_op.HasField('eq'):
                return getattr(model, field) == timestamp_op.eq
            elif timestamp_op.HasField('lt'):
                return getattr(model, field) < timestamp_op.lt
            elif timestamp_op.HasField('gt'):
                return getattr(model, field) > timestamp_op.gt
        logger.warning(f"Unknown operation for field {field}: {operation}")
        return True

    @staticmethod
    def apply_order_by(query, order_by):
        field_path = order_by.field.split('.')
        if len(field_path) > 1:
            # Nested ordering
            related_model = getattr(Product, field_path[0]).property.mapper.class_
            order_field = getattr(related_model, field_path[1])
        else:
            order_field = getattr(Product, order_by.field)
        
        direction = asc if order_by.direction == item_pb2.OrderBy.ASC else desc
        return query.order_by(direction(order_field))

    @staticmethod
    def apply_nested_filter(nested_responses, nested_filter):
        filtered_responses = []
        for response in nested_responses:
            if ProductService.matches_filter(response, nested_filter.filter):
                filtered_responses.append(response)
        
        # Sort filtered responses
        for order_by in nested_filter.order_by:
            filtered_responses.sort(
                key=lambda x: getattr(x, order_by.field),
                reverse=(order_by.direction == item_pb2.OrderBy.DESC)
            )
        
        # Apply pagination
        start = nested_filter.pagination.skip
        end = start + nested_filter.pagination.limit if nested_filter.pagination.limit > 0 else None
        del nested_responses[:]
        nested_responses.extend(filtered_responses[start:end])

    @staticmethod
    def matches_filter(response, filter):
        condition = filter.WhichOneof('condition')
        if condition == 'and':
            and_filter = getattr(filter, 'and')
            return all(ProductService.matches_filter(response, subfilter) for subfilter in and_filter.filters)
        elif condition == 'or':
            or_filter = getattr(filter, 'or')
            return any(ProductService.matches_filter(response, subfilter) for subfilter in or_filter.filters)
        elif condition == 'not':
            not_filter = getattr(filter, 'not')
            return not ProductService.matches_filter(response, not_filter.filter)
        elif condition == 'field':
            return ProductService.matches_field_filter(response, filter.field)
        return True

    @staticmethod
    def matches_field_filter(response, field_filter):
        field_value = getattr(response, field_filter.field)
        operation = field_filter.WhichOneof('operation')
        if operation == 'string_op':
            string_op = field_filter.string_op
            if string_op.HasField('eq'):
                return field_value == string_op.eq
            elif string_op.HasField('like'):
                return string_op.like in field_value
        elif operation == 'int_op':
            int_op = field_filter.int_op
            if int_op.HasField('eq'):
                return field_value == int_op.eq
            elif int_op.HasField('lt'):
                return field_value < int_op.lt
            elif int_op.HasField('gt'):
                return field_value > int_op.gt
        elif operation == 'timestamp_op':
            timestamp_op = field_filter.timestamp_op
            if timestamp_op.HasField('eq'):
                return field_value == timestamp_op.eq
            elif timestamp_op.HasField('lt'):
                return field_value < timestamp_op.lt
            elif timestamp_op.HasField('gt'):
                return field_value > timestamp_op.gt
        return True

    @staticmethod
    def mask_response(response, field_mask):
        all_fields = set(field_mask.paths)
        for field in list(response.DESCRIPTOR.fields_by_name.keys()):
            if field not in all_fields and not any(f.startswith(f"{field}.") for f in all_fields):
                response.ClearField(field)
            elif hasattr(response, field):
                value = getattr(response, field)
                if isinstance(value, (list, containers.RepeatedCompositeFieldContainer)):
                    for item in value:
                        ProductService.mask_response(item, field_mask)
                elif isinstance(value, message.Message):
                    ProductService.mask_response(value, field_mask)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    item_pb2_grpc.add_ProductServiceServicer_to_server(ProductService(), server)
    SERVICE_NAMES = (
        item_pb2.DESCRIPTOR.services_by_name['ProductService'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    server.add_insecure_port('[::]:50051')
    logger.info("Starting server on port 50051...")
    server.start()
    logger.info("Server started.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()