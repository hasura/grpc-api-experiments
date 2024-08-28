# Technical RFC: Proto-based API output of DDN (Alternative to GraphQL and REST)

## Introduction

This document outlines the key features of our Protocol Buffers (proto3) based API. Our design leverages the strengths of Protocol Buffers and gRPC while incorporating concepts familiar to GraphQL users. This approach aims to provide a flexible, efficient, and strongly-typed API that supports complex querying capabilities. 


## Comparison of GraphQL and gRPC

- **Strong Typing**
  - gRPC's type system supports strong typing with a wide range of scalar types, complex message types, enumerations, and more.
  - Allows for precise data modeling.

- **Nested Messages**
  - gRPC allows nested messages.
  - Enables the construction of complex data structures.

- **Field Masks**
  - gRPC uses field masks, which function similarly to GraphQL selection sets.
  - Allows clients to specify the subset of fields they are interested in.

- **Protobuf Definitions**
  - The GraphQL schema of types translates into the protobuf definitions of gRPC messages.
  - GraphQL root operations map to the protobuf definitions of gRPC services (collections of RPC functions).

- **Protobuf Code Generation**
  - Protobuf can generate client and server code in multiple programming languages directly from the `.proto` files.
  - Ensures consistency and reduces the risk of errors.

- **Default Values and Field Options**
  - Fields in gRPC can have default values and other options.
  - For example, you can specify default values for fields, making the API more robust.

## Implementation Strategy

- **Server and Client Responsibilities**
  - The protobuf file, owned and maintained by the API producer, is shared with the API consumer.
  - The API consumer can use any tooling to generate client-side code dynamically.

- **Client SDK Generation**
  - The client will generate the SDK based on the shared protobuf file.

- **Version Management**
  - The API producer will maintain multiple versions of the server (e.g., Proto1 and Proto2).
  - Allows the API consumer to update their clients immediately or maintain different client versions as needed.


## Protobuf Characteristics

Protobuf messages are serialized into a binary format, which makes them compact and efficient for network transmission.

* **Significance of Field Numbers**: Each field in a Protobuf message has a unique number, which is used to identify the field when the message is serialized. These numbers help in efficient encoding and decoding.  
* **Backward Compatibility**: gRPC allows for backward-compatible changes through field numbering, making it easier to evolve APIs without breaking clients.

```protobuf
message User {
  int32 id = 1; // Field number 1
  string name = 2; // Field number 2
  string email = 3; // Field number 3
}

//In this example, id, name, and email have field numbers 1, 2, and 3 respectively. These numbers are used during serialization.
```

A simple GraphQL schema like \-

```graphQL
schema {
  query: Query
}

type Query {
  sayHello(request: HelloRequest): HelloReply
}

type HelloRequest {
  name: Person!
}

type Person {
  name: String!
  id: Int!
  has_ponycopter: Boolean
}

type HelloReply {
  message: String!
}
```

Can be defined in protobuf such as \-

```protobuf
// The greeter service definition.
service Greeter {
  rpc SayHello (HelloRequest) returns (HelloReply) {}
}

message HelloRequest {
  Person name = 1;
}

message Person {
  string name = 1;
  int32 id = 2;
  bool has_ponycopter = 3;
}

message HelloReply {
  string message = 1;
}
```

## API Features

These features demonstrate our API's flexible design, incorporating many concepts similar to those found in GraphQL while leveraging the strengths of Protocol Buffers and gRPC. The following sections detail 15 features of our API: 

### 1. Strong Typing

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

### 2. Field Masks

Description: Field masks allow clients to specify which fields they want to retrieve or update, similar to GraphQL's field selection. This feature enables efficient data transfer by only sending requested fields.

Proto config:
```protobuf
import "google/protobuf/field_mask.proto";

message ProductRequest {
    string id = 1;
    google.protobuf.FieldMask field_mask = 2;
}
```

Sample Go Client Code

```go
FieldMask: &fieldmaskpb.FieldMask{
	Paths: []string{"id", "name", "price", "description", "manufacturer.name"},}
```

### 3. Pagination

Description: Our API implements offset-based pagination, allowing clients to request a specific subset of results and uses offset and limit.

Proto config:
```protobuf
message ProductListRequest {
    int32 offset = 1;
    int32 limit = 2;
    // ...
}
```

### 4. Sorting (Order By)

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

### 5. Boolean Expressions / Filtering

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

### 6. Nested Filtering

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

### 7. Repeated Fields

Description: Our proto uses repeated fields to represent lists or arrays of items, similar to GraphQL's list types.

Proto config:
```protobuf
message ProductResponse {
    // ...
    repeated ReviewResponse reviews = 13;
}
```

### 8. Nested Objects

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

### 9. Enumerations

Description: Our proto uses enumerations to define a set of named constants, similar to GraphQL's enum types.

Proto config:
```protobuf
enum OperatorType {
    EQUALS = 0;
    NOT_EQUALS = 1;
    // ...
}
```

### 10. Service Definition

Description: The proto defines a service with RPC methods, similar to GraphQL's mutation and query types.

Proto config:
```protobuf
service ProductService {
    rpc GetProduct (ProductRequest) returns (ProductResponse);
    rpc ListProducts (ProductListRequest) returns (ProductListResponse);
}
```

### 11. Oneof Fields

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

### 12. Total Count for Pagination

Description: The API includes a total count field in the list response, allowing clients to implement pagination UI elements.

Proto config:
```protobuf
message ProductListResponse {
    repeated ProductResponse products = 1;
    int32 total_count = 2;
}
```

### 13. Relationships (Nested and Referenced Objects)

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

### 14. Many-to-One Relationships

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
The implementation of these relationships in the proto file is similar to how they might be handled in GraphQL:

In GraphQL, you might define types with fields that reference other types.
In this proto, we have messages with fields that reference other messages (either by ID or by including the entire message).

### 15. Commands

Commands become RPC Messages

```protobuf
service ProductService {
  rpc CreateProduct (ProductCreate) returns (ProductResponse);
}

message ProductCreate {
  string name = 1;
  string description = 2;
  int32 price = 3;
  string manufacturer_id = 4;
  string category_id = 5;
  string image = 6;
  string country_of_origin = 7;
}

message ProductResponse {
  string id = 1;
  string name = 2;
  string description = 3;
  int32 price = 4;
  string manufacturer_id = 5;
  string category_id = 6;
  string image = 7;
  string country_of_origin = 8;
}
```

## Open Questions

- API Features (Proto Definition/DDN Metadata)
  - Filter in Relationships
  - Nested Filtering for Relationships:
  - Relationship to Command (Computed Fields)
  - Fields with Arguments (Computed Fields)
  - What about bi directionality?
  
- DX Related
  - How will DDN supply the proto file to the user?  
  - What if the proto changes?  
    - [https://buf.build/product/bsr](https://buf.build/product/bsr)  
  - Supergraph Builds  
    - Console using v1 of the API , V2 version of the gRPC API  




