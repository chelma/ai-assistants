# typed: strict
# frozen_string_literal: true

# PATTERN DEMONSTRATED: Controller (HTTP Layer)
#
# This is YOUR controller that wires the generated mixin to your endpoint.
# Minimal code: include mixin, provide #endpoint accessor.
#
# KEY CONCEPT: Controller delegates to endpoint for business logic
#
# Location: app/controllers/{domain}_engine/v{version}/{resource}_controller.rb

module ActionsEngine
  module V2
    # @owners { team: unified-workflow, domain: actions }  # ← CODEOWNERS annotation
    class ActionPartnershipsController < ApplicationController
      include ActionsAPI::V2::ActionPartnershipsEndpoint::Controller  # ← CRITICAL: Include generated mixin
      extend T::Sig

      # CRITICAL: Provide #endpoint accessor for generated controller methods
      sig { returns(ActionPartnerships::Endpoint) }
      def endpoint
        # PATTERN: Memoize endpoint instance
        @endpoint ||= T.let(
          ActionPartnerships::Endpoint.new,
          T.nilable(ActionPartnerships::Endpoint),
        )
      end

      # TODO: Override actions for custom behavior (rare)
      # def index
      #   # Custom pre-processing
      #   super  # Call generated implementation
      #   # Custom post-processing
      # end

      # TODO: Add before_action filters if needed
      # before_action :authenticate_user!
      # before_action :set_context
    end
  end
end
