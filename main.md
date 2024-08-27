# Technical RFC: Key Features of Our Proto-based API

## Introduction

This document outlines the key features of our Protocol Buffers (proto3) based API. Our design leverages the strengths of Protocol Buffers and gRPC while incorporating concepts familiar to GraphQL users. This approach aims to provide a flexible, efficient, and strongly-typed API that supports complex querying capabilities. The following sections detail 15 core features of our API, including code snippets from our proto file to illustrate each concept.

## 1. Strong Typing

Description: Our proto file demonstrates strong typing, similar to GraphQL's type system. Each field in the messages is explicitly typed, ensuring type safety and reducing runtime errors.

Proto config:
```protobuf
message ProductResponse {
    string id = 1;
    string name = 2;
    int32 price = 4;
    // ...
}
```

## 2. Field Masks

Description: Field masks allow clients to specify which fields they want to retrieve or update, similar to GraphQL's field selection. This feature enables efficient data transfer by only sending requested fields.

Proto config:
```protobuf
message ProductResponse {
    string id = 1;
    string name = 2;
    int32 price = 4;
    // ...
}

## 1. Strong Typing

Description: Our proto file demonstrates strong typing, similar to GraphQL's type system. Each field in the messages is explicitly typed, ensuring type safety and reducing runtime errors.

Proto config:
```protobuf
import "google/protobuf/field_mask.proto";

message ProductRequest {
    string id = 1;
    google.protobuf.FieldMask field_mask = 2;
}
```

## 3. Pagination

Description: Our API implements offset-based pagination, allowing clients to request a specific subset of results. This is similar to GraphQL's cursor-based pagination but uses offset and limit instead.

Proto config:
```protobuf
message ProductListRequest {
    int32 offset = 1;
    int32 limit = 2;
    // ...
}
```

## 1. Strong Typing

Description: Our proto file demonstrates strong typing, similar to GraphQL's type system. Each field in the messages is explicitly typed, ensuring type safety and reducing runtime errors.

Proto config:
```protobuf
message ProductResponse {
    string id = 1;
    string name = 2;
    int32 price = 4;
    // ...
}

## 4. Sorting (Order By)

Description: The API supports sorting results based on specified fields and directions, similar to GraphQL's orderBy argument.

Proto config:
```protobuf
message ProductListRequest {
    // ...
    repeated OrderByField order_by = 3;
    // ...
}

message OrderByField {
    string field = 1;
    SortDirection direction = 2;
}

enum SortDirection {
    SORT_DIRECTION_UNSPECIFIED = 0;
    SORT_ASCENDING = 1;
    SORT_DESCENDING = 2;
}
```

## 5. Boolean Expressions / Filtering

Description: Our API implements a flexible filtering system using a map of field names to filter criteria, similar to GraphQL's where argument.

Proto config:
```protobuf
message ProductListRequest {
    // ...
    map<string, FilterCriteria> where = 4;
    // ...
}

message FilterCriteria {
    OperatorType operator = 1;
    oneof value {
        string string_value = 2;
        int32 int_value = 3;
        bool bool_value = 4;
        double float_value = 5;
    }
}

enum OperatorType {
    EQUALS = 0;
    NOT_EQUALS = 1;
    GREATER_THAN = 2;
    LESS_THAN = 3;
    GREATER_THAN_OR_EQUALS = 4;
    LESS_THAN_OR_EQUALS = 5;
    LIKE = 6;
    IN = 7;
    NOT_IN = 8;
}
```

## 6. Nested Filtering

Description: The API supports nested filtering for related entities, allowing clients to filter on nested fields, similar to GraphQL's nested queries.

Proto config:
```protobuf
message ProductListRequest {
    // ...
    map<string, NestedFilter> nested_filters = 6;
}

message NestedFilter {
    int32 offset = 1;
    int32 limit = 2;
    repeated OrderByField order_by = 3;
    map<string, FilterCriteria> where = 4;
    google.protobuf.FieldMask field_mask = 5;
}
```

## 7. Repeated Fields

Description: Our proto uses repeated fields to represent lists or arrays of items, similar to GraphQL's list types.

Proto config:
```protobuf
message ProductResponse {
    // ...
    repeated ReviewResponse reviews = 13;
}
```

## 8. Nested Objects

Description: The API supports nested objects, allowing for complex data structures similar to GraphQL's nested types.

Proto config:
```protobuf
message ProductResponse {
    // ...
    ManufacturerResponse manufacturer = 9;
    CategoryResponse category = 10;
    // ...
}
```

## 9. Enumerations

Description: Our proto uses enumerations to define a set of named constants, similar to GraphQL's enum types.

Proto config:
```protobuf
enum OperatorType {
    EQUALS = 0;
    NOT_EQUALS = 1;
    // ...
}
```

## 10. Service Definition

Description: The proto defines a service with RPC methods, similar to GraphQL's mutation and query types.

Proto config:
```protobuf
service ProductService {
    rpc GetProduct (ProductRequest) returns (ProductResponse);
    rpc ListProducts (ProductListRequest) returns (ProductListResponse);
}
```

## 11. Oneof Fields

Description: Our proto uses oneof fields to represent mutually exclusive values, similar to GraphQL's union types.

Proto config:
```protobuf
message FilterCriteria {
    OperatorType operator = 1;
    oneof value {
        string string_value = 2;
        int32 int_value = 3;
        bool bool_value = 4;
        double float_value = 5;
    }
}
```

## 12. Oneof Fields

Description: The API includes a total count field in the list response, allowing clients to implement pagination UI elements.

Proto config:
```protobuf
message ProductListResponse {
    repeated ProductResponse products = 1;
    int32 total_count = 2;
}
```

## 13. Relationships (Nested and Referenced Objects)

Description: Our API implements relationships between entities using both nested objects and referenced objects, providing flexibility similar to GraphQL's relationship handling.

Proto config:
```protobuf
message ProductResponse {
    // ...
    string manufacturer_id = 5;  // Referenced object
    string category_id = 6;      // Referenced object
    ManufacturerResponse manufacturer = 9;  // Nested object
    CategoryResponse category = 10;         // Nested object
    repeated ReviewResponse reviews = 13;   // One-to-many relationship
    // ...
}
```

## 14. Many-to-One Relationships

Description: The API includes many-to-one relationships, which are common in data modeling and similar to GraphQL's ability to model relationships where many entities can be associated with one parent entity.

Proto config:
```protobuf
message ProductResponse {
    // ...
    string manufacturer_id = 5;  // Many products to one manufacturer
    string category_id = 6;      // Many products to one category
    // ...
}

message ReviewResponse {
    string id = 1;
    string product_id = 2;  // Many reviews to one product
    string user_id = 3;     // Many reviews to one user
    // ...
}
```

These features demonstrate our API's comprehensive and flexible design, incorporating many concepts similar to those found in GraphQL while leveraging the strengths of Protocol Buffers and gRPC.


