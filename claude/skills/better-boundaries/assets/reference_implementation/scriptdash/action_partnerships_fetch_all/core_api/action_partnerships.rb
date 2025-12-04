# typed: strict

# PATTERN DEMONSTRATED: Core API Wiring (Local/RPC Switching)
#
# This module wires up the Engine client and configures local vs RPC mode.
# Enables seamless upgrade: local method calls → RPC calls via ENV config.
#
// KEY CONCEPT: Core::API provides dotted accessor + automatic local/RPC switching
#
# Location: app/services/{domain}/action_partnerships.rb

module Actions
  # @owners { team: care, domain: actions, followers: [unified-workflow] }
  module ActionPartnerships
    extend T::Sig
    include Core::API  # ← CRITICAL: Enables Core::API features

    # PATTERN: Add Engine's generated client
    # This gives us: #action_partnerships_endpoint accessor + #fetch_all method
    add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client

    # PATTERN: Configure local endpoint (when not using RPC)
    # Points to Engine's endpoint implementation
    self.action_partnerships_endpoint = ActionsEngine::ActionPartnerships::Endpoint

    # WHAT THIS GENERATES:
    # - Actions::ActionPartnerships.fetch_all → calls client.fetch_all
    # - Client checks: use local endpoint or RPC? (based on ENV)
    # - If ENV['ACTIONS_API_BASE_URL'] set → RPC call
    # - If ENV['ALTO_DISABLE_RPC_ACTIONS_API'] = 'true' → local call
    # - Otherwise → local if endpoint configured, RPC if not

    # TODO: For RPC-only setup (Engine deployed separately):
    # 1. Remove `self.action_partnerships_endpoint = ...` line
    # 2. Set ENV['ACTIONS_API_BASE_URL'] = 'https://actions.prod.alto.com'
    # 3. Client will automatically use RPC
  end
end

# ALTERNATIVE: Conditional configuration (based on database availability)
# Rails.application.reloader.to_prepare do
#   if ActiveRecord::Base.configurations.find_db_config(:actions).present? &&
#      !Core::API::RPCClient.use_rpc?(service: 'actions_api')
#     Actions::ActionPartnerships.action_partnerships_endpoint =
#       ActionsEngine::ActionPartnerships::Endpoint
#   end
# end
