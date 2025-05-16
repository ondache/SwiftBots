The example demonstrates how to use remote bots and manage their communication through *gRPC*. 
Though, other protocols such as *REST*, *GraphQL* or *SOAP* could also be used.  

This example features two bot applications: 
- **Weather Bot**: acts as a *server*, receiving requests.  
- **Admin Bot** acts as a *client*, sending requests to the *server*.  

To get started with *gRPC* with the framework as shown in this example, follow these steps:  
- Refer to the official documentation: https://grpc.io/docs/languages/python/quickstart/  
- Create a `.proto` file to define the protocol for communication between *client(s)* and *server*.  
- Generate the required python modules (`*_bp2.py`, `*_pb2.pyi` and `*_pb2_grpc.py`) using the following command:  
  ```bash
  python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. ./bots_admin.proto
  ```  
- Create a gRPC bot in the *server* application.
  It is recommended to inherit from `StubBot`, as it doesn't require to implement `sender` method
  (see the example in `weather_bot.py`)  
- Implement the servicer from the generated `*_pb2_grpc.py` module  
- Implement `listen` method in the *server* bot as illustrated in the example  
- And for the *clients* use *stubs* from the generated `*_pb2_grpc.py` module to send request to the *server*.  