# GENERATED CODE - DO NOT EDIT
#
# PATTERN DEMONSTRATED: Generated Controller Module
#
# This module provides Rails controller actions (index, show, create, etc.)
# Include this in your controller to get HTTP handling automatically.
#
# KEY CONCEPT: Controller calls #endpoint accessor (YOU provide this)
#
# Generated location: {domain}_api/lib/{domain}_api/v{version}/{resource}_endpoint/controller.rb

module ActionsAPI::V2::ActionPartnershipsEndpoint::Controller
  include ActionsAPI::V2::ActionPartnershipsEndpoint::Interface

  # PATTERN: #index action maps to FetchAll RPC
  def index
    # TODO: Handle request params extraction (generated code does this automatically)
    data = endpoint.fetch_all  # ← Calls YOUR endpoint implementation
    response = ActionPartnershipsEndpointFetchAllResponse.new(data: data)
    render(json: response.serialize, status: :ok)
  rescue => e
    # TODO: Error handling (generated code includes standardized error responses)
  end

  # TODO: Other RPC methods generate their own actions:
  # - FetchOne → show
  # - Create → create
  # - Update → update
  # - Delete → destroy
end
