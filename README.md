# grpc-api-experiments


## Server Instructions

python3 -m venv venv-grpc
source venv-grpc/bin/activate
pip install grpcio grpcio-tools grpcio-reflection sqlalchemy psycopg2-binary
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. item.proto
export DATABASE_URL="postgresql://read_only_user:readonlyuser@35.236.11.122:5432/v3-docs-sample-app"
python grpc_server.py

## Client Intstructions


### Using grpcui

Raw Request

```bash

grpcurl -plaintext -d '{
  "base_request": {
    "pagination": {
      "skip": 1,
      "limit": 5
    },
    "order_by": [
      {
        "field": "category.name",
        "direction": "DESC"
      }
    ],
    "filter": {
      "and": {
        "filters": [
          {
            "field": {
              "field": "country_of_origin",
              "string_op": {
                "eq": "US"
              }
            }
          },
          {
            "field": {
              "field": "category.name",
              "string_op": {
                "eq": "T-Shirts"
              }
            }
          }
        ]
      }
    },
    "field_mask": {
      "paths": ["id", "name", "price", "description", "manufacturer.name"]
    }
  },
  "nested_filters": {
    "review_filter": {
      "pagination": {
        "skip": 0,
        "limit": 3
      },
      "order_by": [
        {
          "field": "rating",
          "direction": "ASC"
        }
      ],
      "filter": {
        "field": {
          "field": "created_at",
          "timestamp_op": {
            "gt": "2023-10-15T00:00:00Z"
          }
        }
      },
      "field_mask": {
        "paths": ["rating", "text"]
      }
    }
  }
}' localhost:50051 item.ProductService/ListProducts
```

can also use

grpcui -plaintext localhost:50051
