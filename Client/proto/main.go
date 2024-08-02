package main

import (
	"context"
	"encoding/json"
	"fmt"
	"grpc-client-test/item"
	"log"
	"strings"
	"time"

	"github.com/fatih/color"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/types/known/fieldmaskpb"
)

var (
	keyColor    = color.New(color.FgHiBlue).SprintFunc()
	stringColor = color.New(color.FgHiGreen).SprintFunc()
	numberColor = color.New(color.FgHiMagenta).SprintFunc()
	boolColor   = color.New(color.FgHiRed).SprintFunc()
	nullColor   = color.New(color.FgHiCyan).SprintFunc()
)

func main() {
	// Set up a connection to the server.
	conn, err := grpc.Dial("localhost:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("did not connect: %v", err)
	}
	defer conn.Close()

	// Create a new client
	client := item.NewProductServiceClient(conn)

	// Set up a context with a timeout
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()

	// Build the request
	request := buildComplexListProductsRequest()

	// Make the gRPC call
	response, err := client.ListProducts(ctx, request)
	if err != nil {
		log.Fatalf("Error calling ListProducts: %v", err)
	}

	// Format and print the response
	printColorizedResponse(response)
}

func printColorizedResponse(response *item.ProductListResponse) {
	// Convert proto message to JSON
	marshaler := protojson.MarshalOptions{
		Indent:          "  ",
		EmitUnpopulated: true,
	}
	jsonBytes, err := marshaler.Marshal(response)
	if err != nil {
		log.Fatalf("Failed to marshal response to JSON: %v", err)
	}

	// Pretty print the JSON with colors
	var prettyJSON interface{}
	err = json.Unmarshal(jsonBytes, &prettyJSON)
	if err != nil {
		log.Fatalf("Failed to unmarshal JSON: %v", err)
	}

	fmt.Println("Response:")
	printColorizedJSON(prettyJSON, 0)
}

func printColorizedJSON(data interface{}, indent int) {
	indentStr := strings.Repeat("  ", indent)

	switch v := data.(type) {
	case map[string]interface{}:
		fmt.Println("{")
		keys := make([]string, 0, len(v))
		for k := range v {
			keys = append(keys, k)
		}
		for i, key := range keys {
			fmt.Printf("%s%s: ", indentStr+"  ", keyColor(fmt.Sprintf("%q", key)))
			printColorizedJSON(v[key], indent+1)
			if i < len(keys)-1 {
				fmt.Println(",")
			} else {
				fmt.Println()
			}
		}
		fmt.Print(indentStr + "}")
	case []interface{}:
		fmt.Println("[")
		for i, value := range v {
			fmt.Print(indentStr + "  ")
			printColorizedJSON(value, indent+1)
			if i < len(v)-1 {
				fmt.Println(",")
			} else {
				fmt.Println()
			}
		}
		fmt.Print(indentStr + "]")
	case string:
		fmt.Print(stringColor(fmt.Sprintf("%q", v)))
	case float64:
		fmt.Print(numberColor(v))
	case bool:
		fmt.Print(boolColor(v))
	case nil:
		fmt.Print(nullColor("null"))
	default:
		fmt.Printf("%v", v)
	}

	if indent == 0 {
		fmt.Println()
	}
}

func buildComplexListProductsRequest() *item.ProductListRequest {
	return &item.ProductListRequest{
		BaseRequest: &item.PaginatedFilterRequest{
			Pagination: &item.Pagination{
				Skip:  1,
				Limit: 5,
			},
			Filter: &item.Filter{
				Condition: &item.Filter_And{
					And: &item.AndFilter{
						Filters: []*item.Filter{
							{
								Condition: &item.Filter_Field{
									Field: &item.FieldFilter{
										Field: "country_of_origin",
										Operation: &item.FieldFilter_StringOp{
											StringOp: &item.StringOperation{
												Type: &item.StringOperation_Eq{
													Eq: "US",
												},
											},
										},
									},
								},
							},
							{
								Condition: &item.Filter_Field{
									Field: &item.FieldFilter{
										Field: "category.name",
										Operation: &item.FieldFilter_StringOp{
											StringOp: &item.StringOperation{
												Type: &item.StringOperation_Eq{
													Eq: "T-Shirts",
												},
											},
										},
									},
								},
							},
						},
					},
				},
			},
			OrderBy: []*item.OrderBy{
				{
					Field:     "category.name",
					Direction: item.OrderBy_DESC,
				},
			},
			FieldMask: &fieldmaskpb.FieldMask{
				Paths: []string{"id", "name", "price", "description", "manufacturer.name"},
			},
		},
		NestedFilters: &item.NestedFilters{
			ReviewFilter: &item.PaginatedFilterRequest{
				Pagination: &item.Pagination{
					Skip:  0,
					Limit: 3,
				},
				Filter: &item.Filter{
					Condition: &item.Filter_Field{
						Field: &item.FieldFilter{
							Field: "created_at",
							Operation: &item.FieldFilter_TimestampOp{
								TimestampOp: &item.TimestampOperation{
									Type: &item.TimestampOperation_Gt{
										Gt: "2023-10-15T00:00:00Z",
									},
								},
							},
						},
					},
				},
				OrderBy: []*item.OrderBy{
					{
						Field:     "rating",
						Direction: item.OrderBy_ASC,
					},
				},
				FieldMask: &fieldmaskpb.FieldMask{
					Paths: []string{"rating", "text"},
				},
			},
		},
	}
}
