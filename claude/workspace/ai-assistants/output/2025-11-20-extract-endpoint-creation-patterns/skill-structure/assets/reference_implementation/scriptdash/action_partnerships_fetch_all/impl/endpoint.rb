# typed: strict

# PATTERN DEMONSTRATED: Scriptdash Endpoint (Permissions + Delegation)
#
# This endpoint adds permissions checking, then delegates to Engine via Core::API.
// No business logic here - that lives in the Engine.
#
# KEY CONCEPT: Scriptdash layer = gateway with authorization
#
# Location: app/services/{domain}/wunderbar/{resource}_endpoint.rb

module Actions
  module Wunderbar
    # @owners { team: care, domain: actions, followers: [unified-workflow] }
    class ActionPartnershipsEndpoint < Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Interface::AbstractActionPartnershipsEndpoint
      extend T::Sig
      include Auth::CurrentAbility  # ← CRITICAL: Provides current_ability for permissions
      include Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Interface

      # PATTERN: Check permissions, then delegate to Engine
      sig do
        override.returns(T::Array[ActionsAPI::Types::V2::ActionPartnership])
      end
      def fetch_all
        # CRITICAL: Check permissions BEFORE calling Engine
        # Raises CanCan::AccessDenied if user lacks permission
        current_ability.authorize! :read, ActionsAPI::Types::V2::ActionPartnership

        # PATTERN: Delegate to Engine via Core::API
        # This calls ActionsEngine::ActionPartnerships::Endpoint#fetch_all
        # (either locally or via RPC, depending on ENV configuration)
        Actions.action_partnerships.fetch_all

        # ALTERNATIVE: Add Scriptdash-specific logic before/after delegation
        # results = Actions.action_partnerships.fetch_all
        # results.select { |p| p.company_id == current_company_id }  # Filter by company
      end

      # TODO: For other methods (Create, Update, Delete), check appropriate permissions:
      # def create(params:)
      #   current_ability.authorize! :create, ActionsAPI::Types::V2::ActionPartnership
      #   Actions.action_partnerships.create(params: params)
      # end
      #
      # def update(id:, params:)
      #   current_ability.authorize! :update, ActionsAPI::Types::V2::ActionPartnership
      #   Actions.action_partnerships.update(id: id, params: params)
      # end
    end
  end
end

# WHY THIS PATTERN?
# - Permissions enforced at gateway (Scriptdash)
# - Engine stays permission-agnostic (can serve multiple frontends)
# - Scriptdash can add UI-specific logic without touching Engine
# - Separate deployment: Update permissions without redeploying Engine
