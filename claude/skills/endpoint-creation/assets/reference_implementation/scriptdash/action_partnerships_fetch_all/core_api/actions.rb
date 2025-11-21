# typed: strict

# PATTERN DEMONSTRATED: Dotted Accessor Pattern
#
# This exposes the Core API module via dotted accessor: Actions.action_partnerships
# Enables clean calling syntax throughout Scriptdash.
#
# Location: app/services/actions.rb

module Actions
  extend T::Sig

  # PATTERN: Expose Core API module via class method accessor
  sig { returns(T.class_of(ActionPartnerships)) }
  def self.action_partnerships
    ActionPartnerships  # ← Returns the Core::API module
  end

  # TODO: Add other accessors for other endpoints
  # sig { returns(T.class_of(ActionTypes)) }
  # def self.action_types
  #   ActionTypes
  # end
end

# USAGE anywhere in Scriptdash:
#
# # Fetch all action partnerships (local or RPC, depending on ENV)
# partnerships = Actions.action_partnerships.fetch_all
#
# # Fetch one action partnership
# partnership = Actions.action_partnerships.fetch_one(id: 123)
#
# WHY THIS PATTERN?
# - Clean, discoverable API (Actions.resource.method)
# - Type-safe (Sorbet knows the return types)
# - Consistent with Rails conventions (User.all, Post.find, etc.)
# - Hides Core::API complexity from consumers
