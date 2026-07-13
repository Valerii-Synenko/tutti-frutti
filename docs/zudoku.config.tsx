import type { ZudokuConfig } from "zudoku";

// Run `python scripts/collect_openapi.py` against a running docker-compose
// stack to (re)generate the JSON files referenced below.
const config: ZudokuConfig = {
  metadata: {
    title: "Tutti Frutti — API Reference",
    description: "API documentation for the Tutti Frutti microservices demo.",
  },
  apis: [
    { type: "file", input: "./openapi/gateway.json", path: "/gateway", server: "http://localhost:8080" },
    { type: "file", input: "./openapi/users-service.json", path: "/users", server: "http://localhost:8001" },
    { type: "file", input: "./openapi/catalogue-service.json", path: "/catalogue", server: "http://localhost:8002" },
    { type: "file", input: "./openapi/orders-service.json", path: "/orders", server: "http://localhost:8003" },
    { type: "file", input: "./openapi/fruit-assistant-service.json", path: "/assistant", server: "http://localhost:8004" },
  ],
  navigation: [
    { type: "doc", file: "overview", path: "/", label: "Overview" },
    {
      type: "category",
      label: "APIs",
      items: [
        { type: "link", label: "Gateway (BFF)", to: "/gateway" },
        { type: "link", label: "Users", to: "/users" },
        { type: "link", label: "Catalogue", to: "/catalogue" },
        { type: "link", label: "Orders", to: "/orders" },
        { type: "link", label: "Fruit Assistant", to: "/assistant" },
      ],
    },
  ],
};

export default config;
