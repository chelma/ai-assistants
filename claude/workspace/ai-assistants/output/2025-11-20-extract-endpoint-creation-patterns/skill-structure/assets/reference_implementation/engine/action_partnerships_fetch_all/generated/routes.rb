# GENERATED CODE - DO NOT EDIT
#
# PATTERN DEMONSTRATED: Generated Routes Module
#
# This module provides Rails routes for the endpoint.
# Use `extend` in config/routes.rb to add these routes.
#
# KEY CONCEPT: Service V2.0 maps RPCs to RESTful routes automatically
#
# Generated location: {domain}_api/lib/{domain}_api/v{version}/{resource}_endpoint/routes.rb

module ActionsAPI::V2::ActionPartnershipsEndpoint::Routes
  def self.extended(router)
    router.instance_exec do
      # PATTERN: FetchAll maps to GET /{plural}/fetch_all
      # This is NOT standard REST (which would be GET /{plural})
      # Alto uses explicit method names in URLs for clarity
      namespace :v2 do
        scope :action_partnerships do
          get 'fetch_all',
              action: :index,  # ← Maps to controller#index
              as: :action_partnerships_index,
              controller: 'action_partnerships'

          # TODO: Other RPCs generate their own routes:
          # get ':id', action: :show, as: :action_partnership  # FetchOne
          # post '', action: :create  # Create
          # put ':id', action: :update  # Update
          # delete ':id', action: :destroy  # Delete
        end
      end
    end
  end
end

# USAGE in config/routes.rb:
# ActionsEngine::Engine.routes.draw do
#   extend ActionsAPI::V2::ActionPartnershipsEndpoint::Routes
# end
