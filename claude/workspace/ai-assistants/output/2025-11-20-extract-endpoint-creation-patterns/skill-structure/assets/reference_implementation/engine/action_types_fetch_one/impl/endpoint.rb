# typed: strict

# PATTERN DEMONSTRATED: FetchOne Implementation with Adapter Pattern
#
# KEY DIFFERENCES from FetchAll:
# - Takes `id:` parameter (Integer, not Array)
# - Uses Model.find(id) (not Model.all or Model.where)
# - Returns single struct (not Array)
# - Uses adapter for complex mapping
#
# See action_partnerships_fetch_all/impl/endpoint.rb for detailed annotations

module ActionsEngine
  module ActionTypes
    class Endpoint < ActionsAPI::V2::ActionTypesEndpoint::Interface::AbstractActionTypesEndpoint
      extend T::Sig

      # PATTERN: FetchOne signature - id parameter, returns single struct
      sig do
        override.params(id: Integer).returns(ActionsAPI::Types::V2::ActionType)
      end
      def fetch_one(id:)
        # PATTERN: Find specific record by ID
        action_type = ActionType.find(id)  # ← Raises ActiveRecord::RecordNotFound if missing

        # PATTERN: Adapter pattern for complex mapping
        ActionTypeAdapter.new(action_type).to_struct

        # ALTERNATIVE: Direct mapping (if simple)
        # ActionsAPI::Types::V2::ActionType.new(
        #   id: action_type.id,
        #   name: action_type.name,
        #   # ... all fields
        # )
      end

      # TODO: Adapter class pattern (create separate file for complex logic)
      # class ActionTypeAdapter
      #   def initialize(model)
      #     @model = model
      #   end
      #
      #   def to_struct
      #     ActionsAPI::Types::V2::ActionType.new(
      #       id: @model.id,
      #       name: @model.name,
      #       # Complex field transformations here
      #       trigger_type: map_trigger_type(@model.trigger_type),
      #       tags: @model.tags&.split(',') || [],
      #     )
      #   end
      #
      #   private
      #
      #   def map_trigger_type(value)
      #     case value
      #     when 'auto' then TriggerType::AUTO
      #     when 'manual' then TriggerType::MANUAL
      #     end
      #   end
      # end
    end
  end
end
