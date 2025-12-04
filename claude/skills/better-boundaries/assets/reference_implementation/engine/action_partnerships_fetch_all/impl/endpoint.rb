# typed: strict
# frozen_string_literal: true

# PATTERN DEMONSTRATED: Endpoint Implementation (Business Logic)
#
# This is YOUR code that implements the abstract interface.
# Business logic goes here: database queries, transformations, validations.
#
# KEY CONCEPT: Extends generated AbstractEndpoint, implements abstract methods
#
# Location: app/services/{domain}_engine/{resource}/endpoint.rb

module ActionsEngine
  module ActionPartnerships
    # @owners { team: unified-workflow, domain: actions }  # ← CODEOWNERS annotation
    class Endpoint < ActionsAPI::V2::ActionPartnershipsEndpoint::Interface::AbstractActionPartnershipsEndpoint
      extend T::Sig

      # CRITICAL: Use 'override' to ensure method matches abstract signature
      sig do
        override.returns(T::Array[ActionsAPI::Types::V2::ActionPartnership])
      end
      def fetch_all
        # PATTERN: Query database, map to proto structs
        ActionPartnership.all.map do |action_partnership|
          # PATTERN: Map ActiveRecord model → Proto struct
          ActionsAPI::Types::V2::ActionPartnership.new(
            id: action_partnership.id,
            name: action_partnership.name,
            value: action_partnership.value,
          )
        end

        # ALTERNATIVES based on use case:
        #
        # 1. With scopes/filtering:
        #    ActionPartnership.active.where(company_id: current_company_id).map { ... }
        #
        # 2. With eager loading (N+1 prevention):
        #    ActionPartnership.includes(:related_model).all.map { ... }
        #
        # 3. With ordering:
        #    ActionPartnership.order(:name).map { ... }
        #
        # 4. With adapter pattern (for complex mapping):
        #    ActionPartnership.all.map { |ap| ActionPartnershipAdapter.new(ap).to_struct }
      end

      # TODO: Add helper methods for complex mapping
      # private
      #
      # def to_struct(action_partnership)
      #   ActionsAPI::Types::V2::ActionPartnership.new(
      #     id: action_partnership.id,
      #     # ... complex field mappings
      #   )
      # end
    end
  end
end
