# GENERATED CODE - DO NOT EDIT
# PATTERN DEMONSTRATED: Generated Abstract Interface from Proto
# LOCATION: operations_api/lib/operations_api/v1/wunderbar_users_endpoint/interface.rb
# KEY CONCEPT: Scriptdash implementation will extend AbstractWunderbarUsersEndpoint

# typed: strict

module OperationsAPI
  module V1
    module WunderbarUsersEndpoint
      module Interface
        # Request type for FetchOne
        class WunderbarUsersEndpointFetchOneRequest < T::Struct
          const :id, Integer
        end

        # Response type for FetchOne
        class WunderbarUsersEndpointFetchOneResponse < T::Struct
          const :errors, T.nilable(T::Array[Core::Types::V1::ErrorObject])
          const :data, T.nilable(OperationsAPI::Types::V1::WunderbarUser)
        end

        # Request type for FetchAll
        class WunderbarUsersEndpointFetchAllRequest < T::Struct
          const :ids, T.nilable(T::Array[Integer])
        end

        # Response type for FetchAll
        class WunderbarUsersEndpointFetchAllResponse < T::Struct
          const :errors, T.nilable(T::Array[Core::Types::V1::ErrorObject])
          const :data, T.nilable(T::Array[OperationsAPI::Types::V1::WunderbarUser])
        end

        # CRITICAL: Abstract endpoint that Scriptdash must implement
        class AbstractWunderbarUsersEndpoint
          extend T::Sig
          extend T::Helpers
          abstract!

          # Scriptdash must implement this method
          sig do
            abstract
              .params(id: Integer)
              .returns(OperationsAPI::Types::V1::WunderbarUser)
          end
          def fetch_one(id:); end

          # Scriptdash must implement this method
          sig do
            abstract
              .params(ids: T.nilable(T::Array[Integer]))
              .returns(T::Array[OperationsAPI::Types::V1::WunderbarUser])
          end
          def fetch_all(ids: nil); end
        end
      end
    end
  end
end
