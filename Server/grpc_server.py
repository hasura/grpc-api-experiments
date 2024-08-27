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
from google.protobuf import field_mask_pb2
import traceback

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
                self.apply_field_mask(response, request.field_mask)

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
            logger.debug(f"Initial query created")

            # Apply filtering
            if request.where:
                try:
                    filter_condition = self.apply_filters(request.where)
                    query = query.filter(filter_condition)
                    logger.debug(f"Filters applied: {request.where}")
                except Exception as e:
                    logger.error(f"Error applying filters: {e}")
                    logger.error(traceback.format_exc())
                    return self.handle_error(context, f"Error applying filters: {str(e)}")

            # Apply ordering
            try:
                for order_by in request.order_by:
                    direction = desc if order_by.startswith('-') else asc
                    field = order_by[1:] if order_by.startswith('-') else order_by
                    if '.' in field:
                        related_name, attr = field.split('.')
                        related_model = getattr(Product, related_name).property.mapper.class_
                        query = query.join(related_model).order_by(direction(getattr(related_model, attr)))
                    else:
                        query = query.order_by(direction(getattr(Product, field)))
                logger.debug(f"Ordering applied: {request.order_by}")
            except Exception as e:
                logger.error(f"Error applying ordering: {e}")
                logger.error(traceback.format_exc())
                return self.handle_error(context, f"Error applying ordering: {str(e)}")

            # Print the SQL query
            logger.debug(f"Generated SQL query: {query.statement.compile(compile_kwargs={'literal_binds': True})}")

            # Get total count before pagination
            try:
                total_count = query.count()
                logger.debug(f"Total count before pagination: {total_count}")
            except Exception as e:
                logger.error(f"Error getting total count: {e}")
                logger.error(traceback.format_exc())
                return self.handle_error(context, f"Error getting total count: {str(e)}")

            # Apply pagination
            query = query.offset(request.offset).limit(request.limit)
            logger.debug(f"Pagination applied: offset={request.offset}, limit={request.limit}")

            try:
                db_products = query.all()
                logger.debug(f"Number of products fetched after pagination: {len(db_products)}")
            except Exception as e:
                logger.error(f"Error fetching products: {e}")
                logger.error(traceback.format_exc())
                return self.handle_error(context, f"Error fetching products: {str(e)}")

            response = item_pb2.ProductListResponse()
            response.total_count = total_count

            for db_product in db_products:
                try:
                    product_response = self.product_to_response(db_product)
                    logger.debug(f"Product converted to response: ID={db_product.id}")

                    # Apply nested filters
                    if request.nested_filters:
                        for filter_type, nested_filter in request.nested_filters.items():
                            logger.debug(f"Applying nested filter: {filter_type}")
                            if filter_type == "REVIEWS":
                                try:
                                    original_review_count = len(product_response.reviews)
                                    self.apply_nested_filter(product_response.reviews, nested_filter)
                                    logger.debug(f"Nested filter applied to reviews: before={original_review_count}, after={len(product_response.reviews)}")
                                except Exception as e:
                                    logger.error(f"Error applying nested filter to reviews: {e}")
                                    logger.error(traceback.format_exc())

                    if request.field_mask.paths:
                        try:
                            logger.debug(f"Applying field mask: {request.field_mask.paths}")
                            self.apply_field_mask(product_response, request.field_mask)
                            logger.debug(f"Field mask applied successfully")
                        except Exception as e:
                            logger.error(f"Error applying field mask: {e}")
                            logger.error(traceback.format_exc())

                    response.products.append(product_response)
                    logger.debug(f"Product added to response: ID={db_product.id}")
                except Exception as e:
                    logger.error(f"Error processing product {db_product.id}: {e}")
                    logger.error(traceback.format_exc())
                    # Continue processing other products

            logger.info(f"ListProducts request processed successfully. Returning {len(response.products)} products out of {total_count} total.")
            return response
        except Exception as e:
            logger.error(f"Unexpected error in ListProducts: {e}")
            logger.error(traceback.format_exc())
            return self.handle_error(context, f"Unexpected error: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def handle_error(context, message):
        logger.error(message)
        context.abort(grpc.StatusCode.INTERNAL, message)

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
            review_response.rating = review.rating if hasattr(review, 'rating') else 0  # Default to 0 if rating is missing
            review_response.text = review.text
            review_response.is_visible = review.is_visible
            review_response.created_at = str(review.created_at)
            review_response.updated_at = str(review.updated_at)

        return response

    @staticmethod
    def apply_filters(filters):
        conditions = []
        for field, filter_criteria in filters.items():
            condition = ProductService.apply_filter_criteria(field, filter_criteria)
            conditions.append(condition)
        return and_(*conditions)

    
    @staticmethod
    def apply_filter_criteria(field, filter_criteria):
        if '.' in field:
            related_name, attr = field.split('.')
            related_model = getattr(Product, related_name).property.mapper.class_
            subq = select(related_model).where(
                and_(
                    getattr(Product, f"{related_name}_id") == related_model.id,
                    ProductService.create_filter_condition(getattr(related_model, attr), filter_criteria)
                )
            ).correlate(Product)
            return exists(subq)
        else:
            return ProductService.create_filter_condition(getattr(Product, field), filter_criteria)

    @staticmethod
    def create_filter_condition(field_attr, filter_criteria):
        value = getattr(filter_criteria, filter_criteria.WhichOneof('value'))

        operator_map = {
            item_pb2.OperatorType.EQUALS: lambda f, v: f == v,
            item_pb2.OperatorType.NOT_EQUALS: lambda f, v: f != v,
            item_pb2.OperatorType.GREATER_THAN: lambda f, v: f > v,
            item_pb2.OperatorType.LESS_THAN: lambda f, v: f < v,
            item_pb2.OperatorType.GREATER_THAN_OR_EQUALS: lambda f, v: f >= v,
            item_pb2.OperatorType.LESS_THAN_OR_EQUALS: lambda f, v: f <= v,
            item_pb2.OperatorType.LIKE: lambda f, v: f.like(f"%{v}%"),
            item_pb2.OperatorType.IN: lambda f, v: f.in_(v.split(',') if isinstance(v, str) else v),
            item_pb2.OperatorType.NOT_IN: lambda f, v: ~f.in_(v.split(',') if isinstance(v, str) else v),
        }

        operation = operator_map.get(filter_criteria.operator)
        if operation:
            return operation(field_attr, value)
        else:
            logger.warning(f"Unsupported operator: {filter_criteria.operator}")
            return True

    @staticmethod
    def apply_nested_filter(nested_responses, nested_filter):
        try:
            filtered_responses = [
                response for response in nested_responses
                if ProductService.matches_filter(response, nested_filter.where)
            ]

            # Sort filtered responses
            for order_by in nested_filter.order_by:
                reverse = order_by.startswith('-')
                field = order_by[1:] if reverse else order_by
                filtered_responses.sort(
                    key=lambda x: getattr(x, field, 0),  # Use 0 as default if field doesn't exist
                    reverse=reverse
                )

            # Apply pagination
            start = nested_filter.offset
            end = start + nested_filter.limit if nested_filter.limit > 0 else None
            del nested_responses[:]
            nested_responses.extend(filtered_responses[start:end])

            # Apply field mask
            if nested_filter.field_mask.paths:
                for response in nested_responses:
                    ProductService.apply_field_mask(response, nested_filter.field_mask)
        except Exception as e:
            logger.error(f"Error in apply_nested_filter: {e}")
            logger.error(traceback.format_exc())
        
    @staticmethod
    def matches_filter(response, filters):
        try:
            for field, filter_criteria in filters.items():
                field_value = getattr(response, field, None)
                if field_value is None:
                    logger.warning(f"Field {field} not found in response")
                    return False
                
                value = getattr(filter_criteria, filter_criteria.WhichOneof('value'))
                
                if not ProductService.compare_values(field_value, value, filter_criteria.operator):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error in matches_filter: {e}")
            logger.error(traceback.format_exc())
            return False

    @staticmethod
    def compare_values(field_value, filter_value, operator):
        operator_map = {
            item_pb2.OperatorType.EQUALS: lambda a, b: a == b,
            item_pb2.OperatorType.NOT_EQUALS: lambda a, b: a != b,
            item_pb2.OperatorType.GREATER_THAN: lambda a, b: a > b,
            item_pb2.OperatorType.LESS_THAN: lambda a, b: a < b,
            item_pb2.OperatorType.GREATER_THAN_OR_EQUALS: lambda a, b: a >= b,
            item_pb2.OperatorType.LESS_THAN_OR_EQUALS: lambda a, b: a <= b,
            item_pb2.OperatorType.LIKE: lambda a, b: b.lower() in str(a).lower(),
            item_pb2.OperatorType.IN: lambda a, b: a in b.split(',') if isinstance(b, str) else a in b,
            item_pb2.OperatorType.NOT_IN: lambda a, b: a not in b.split(',') if isinstance(b, str) else a not in b,
        }

        operation = operator_map.get(operator)
        if operation:
            try:
                return operation(field_value, filter_value)
            except Exception as e:
                logger.error(f"Error comparing values {field_value} and {filter_value} with operator {operator}: {e}")
                return False
        else:
            logger.warning(f"Unsupported operator: {operator}")
            return True

    @staticmethod
    def apply_field_mask(response, field_mask):
        if not isinstance(field_mask, field_mask_pb2.FieldMask):
            field_mask = field_mask_pb2.FieldMask(paths=field_mask.paths)
        field_mask.MergeMessage(field_mask, response, response)

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