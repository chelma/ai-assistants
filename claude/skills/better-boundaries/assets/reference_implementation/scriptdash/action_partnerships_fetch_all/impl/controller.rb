# typed: strict

# PATTERN DEMONSTRATED: Scriptdash Controller (HTTP Layer)
#
# Identical pattern to Engine controller, but with different namespace.
//
# KEY CONCEPT: Controller is thin - just wires mixin to endpoint
#
# Location: app/controllers/wunderbar/{domain}/v{version}/{resource}_controller.rb

module Wunderbar
  module Actions
    module V1
      # @owners { team: care, domain: actions, followers: [unified-workflow] }
      class ActionPartnershipsController < WunderbarController  # ← Inherit from WunderbarController
        include Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Controller  # ← Generated mixin
        extend T::Sig

        # CRITICAL: Provide #endpoint accessor (returns Scriptdash endpoint, not Engine)
        sig { returns(::Actions::Wunderbar::ActionPartnershipsEndpoint) }
        def endpoint
          @endpoint ||= T.let(
            ::Actions::Wunderbar::ActionPartnershipsEndpoint.new,  # ← Scriptdash endpoint
            T.nilable(::Actions::Wunderbar::ActionPartnershipsEndpoint),
          )
        end

        # TODO: Add before_action filters (inherited from WunderbarController)
        # before_action :authenticate_wunderbar_user!  # Usually in WunderbarController
        # before_action :set_current_company
      end
    end
  end
end

# KEY DIFFERENCES from Engine controller:
# - Inherits from WunderbarController (not ApplicationController)
# - Uses Scriptdash endpoint (::Actions::Wunderbar::ActionPartnershipsEndpoint)
# - May have Wunderbar-specific filters (authentication, company scoping)
