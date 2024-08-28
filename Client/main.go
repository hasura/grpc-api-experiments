package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strings"
	"time"

	"github.com/fatih/color"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/types/known/fieldmaskpb"

	"client/item"
)

var (
	keyColor    = color.New(color.FgHiBlue).SprintFunc()
	stringColor = color.New(color.FgHiGreen).SprintFunc()
	numberColor = color.New(color.FgHiMagenta).SprintFunc()
	boolColor   = color.New(color.FgHiRed).SprintFunc()
	nullColor   = color.New(color.FgHiCyan).SprintFunc()
)

// Constants for nested filter types
const (
	NestedFilterReviews      = "REVIEWS"
	NestedFilterManufacturer = "MANUFACTURER"
	NestedFilterCategory     = "CATEGORY"
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
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Build the request
	request := buildSimplifiedListProductsRequest()

	// Make the gRPC call
	response, err := client.ListProducts(ctx, request)
	if err != nil {
		log.Fatalf("Error calling ListProducts: %v", err)
	}

	// Format and print the response
	printColorizedResponse(response)
}

func nestedFilterTypeToString(nft item.NestedFilterType) string {
	return item.NestedFilterType_name[int32(nft)]
}

func buildSimplifiedListProductsRequest() *item.ProductListRequest {
	return &item.ProductListRequest{
		Offset: 1,
		Limit:  2,
		OrderBy: []*item.OrderByField{
			{
				Field:     "category.name",
				Direction: item.SortDirection_SORT_DESCENDING,
			},
		},
		Where: map[string]*item.FilterCriteria{
			"country_of_origin": {
				Operator: item.OperatorType_EQUALS,
				Value:    &item.FilterCriteria_StringValue{StringValue: "US"},
			},
			"category.name": {
				Operator: item.OperatorType_EQUALS,
				Value:    &item.FilterCriteria_StringValue{StringValue: "T-Shirts"},
			},
		},
		FieldMask: &fieldmaskpb.FieldMask{
			Paths: []string{"id", "name", "price", "description", "manufacturer.name"},
		},
		NestedFilters: map[string]*item.NestedFilter{
			NestedFilterReviews: {
				Offset: 0,
				Limit:  3,
				OrderBy: []*item.OrderByField{
					{
						Field:     "rating",
						Direction: item.SortDirection_SORT_DESCENDING,
					},
				},
				Where: map[string]*item.FilterCriteria{
					"created_at": {
						Operator: item.OperatorType_GREATER_THAN,
						Value:    &item.FilterCriteria_StringValue{StringValue: "2023-10-15T00:00:00Z"},
					},
				},
				FieldMask: &fieldmaskpb.FieldMask{
					Paths: []string{"rating", "text"},
				},
			},
		},
	}
}

// func buildproductrequest() *item.ProductListRequest{
// 	return &item.ProductListRequest{
// 		Offset: 1,
// 		Limit: 2,
// 		OrderBy: []*item.OrderByField{
// 			{
// 				Field: "category.name",
// 				Direction: item.SortDirection_SORT_ASCENDING,
// 			},
// 		},
// 		Where: map[string]*item.FilterCriteria{
// 			"country_of_origin": {
// 				Value: &item.FilterCriteria_StringValue{StringValue: "US"},
// 				Operator: item.OperatorType_EQUALS,
// 			}
// 		},
// 	}
// }

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
