# PATTERN DEMONSTRATED: Scriptdash Implementation of Engine Interface
# LOCATION: scriptdash/app/services/operations/v1/wunderbar_users_endpoint.rb
# KEY CONCEPT: Implements engine's abstract interface but uses Scriptdash models

# typed: strict

module Operations
  module V1
    # CRITICAL: Extends AbstractEndpoint from engine's generated code
    class WunderbarUsersEndpoint < OperationsAPI::V1::WunderbarUsersEndpoint::Interface::AbstractWunderbarUsersEndpoint
      extend T::Sig

      # Include interface for type definitions
      include OperationsAPI::V1::WunderbarUsersEndpoint::Interface

      # PATTERN: FetchOne implementation using Scriptdash model
      # KEY CONCEPT: ::WunderbarUser is a Scriptdash model, not engine model
      sig { override.params(id: Integer).returns(OperationsAPI::Types::V1::WunderbarUser) }
      def fetch_one(id:)
        wb_user = ::WunderbarUser.find(id)  # ← Scriptdash model
        to_struct(wb_user)
      end

      # PATTERN: FetchAll with optional IDs filter
      # KEY CONCEPT: Direct ActiveRecord access to Scriptdash database
      sig do
        override
          .params(ids: T.nilable(T::Array[Integer]))
          .returns(T::Array[OperationsAPI::Types::V1::WunderbarUser])
      end
      def fetch_all(ids: nil)
        # Start with base relation
        rel = ::WunderbarUser.all  # ← Scriptdash model

        # Apply ID filter if provided
        rel = rel.where(id: ids) unless ids.nil?

        # PREFERRED: Eager load associations to avoid N+1
        rel = rel.includes(:wunderbar_roles)

        # Transform to proto structs
        rel.map { |wb_user| to_struct(wb_user) }
      end

      private

      # PATTERN: Model-to-Proto transformation
      # KEY CONCEPT: Maps Scriptdash model attributes to proto type
      sig { params(wb_user: ::WunderbarUser).returns(OperationsAPI::Types::V1::WunderbarUser) }
      def to_struct(wb_user)
        OperationsAPI::Types::V1::WunderbarUser.new(
          id: T.must(wb_user.id),
          email: wb_user.email,
          first_name: wb_user.first_name,
          last_name: wb_user.last_name,
          full_name: wb_user.full_name,
          team: wb_user.team,
          pod: wb_user.pod,
          wunderbar_roles: wb_user.wunderbar_roles.map(&:name),
          created_at: T.must(wb_user.created_at).to_time.to_i,
          updated_at: T.must(wb_user.updated_at).to_time.to_i,
        )
      end
    end
  end
end

# TODO: Replace ::WunderbarUser with your Scriptdash model
# TODO: Update to_struct to map your model's attributes to proto fields
# TODO: Add any business logic (scopes, filters, etc.) as needed
