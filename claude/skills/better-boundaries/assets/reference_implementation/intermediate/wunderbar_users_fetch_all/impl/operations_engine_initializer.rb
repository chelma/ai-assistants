# PATTERN DEMONSTRATED: Engine-to-Scriptdash Implementation Hookup
# LOCATION: scriptdash/config/initializers/operations_engine.rb
# KEY CONCEPT: Tells engine's generated controller to use Scriptdash's implementation
# CRITICAL: This is what makes "proto in engine, impl in Scriptdash" work

# typed: true

Rails.application.reloader.to_prepare do
  # CRITICAL: Set base controller for engine routes
  # This makes engine routes inherit from Scriptdash's APIController
  OperationsEngine::Engine.base_controller = APIController

  # CRITICAL: Hook up Scriptdash implementation to engine interface
  # Format: <Engine>::Engine.<resource>_endpoint = <ScriptdashImplementation>
  # The engine's generated controller will call this endpoint's methods
  OperationsEngine::Engine.wunderbar_users_endpoint = Operations::V1::WunderbarUsersEndpoint

  # PATTERN: Multiple endpoints can be hooked up in same initializer
  # OperationsEngine::Engine.assignments_endpoint = Operations::V1::AssignmentsEndpoint
  # OperationsEngine::Engine.facilities_endpoint = Operations::Facilities::Endpoint
end

# How this works:
# 1. Engine generates controller with: `endpoint.fetch_one(id: params[:id])`
# 2. `endpoint` method checks: `OperationsEngine::Engine.wunderbar_users_endpoint`
# 3. Finds: `Operations::V1::WunderbarUsersEndpoint` (Scriptdash class)
# 4. Calls: `Operations::V1::WunderbarUsersEndpoint.new.fetch_one(id: 123)`
# 5. Your Scriptdash code runs!

# TODO: Replace OperationsEngine with your engine module name
# TODO: Replace wunderbar_users_endpoint with your endpoint accessor name
# TODO: Replace Operations::V1::WunderbarUsersEndpoint with your implementation class
