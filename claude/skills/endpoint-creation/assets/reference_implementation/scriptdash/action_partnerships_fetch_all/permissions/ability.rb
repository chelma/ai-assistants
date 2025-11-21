# typed: false

# PATTERN DEMONSTRATED: CanCanCan Permissions (Ability Class)
#
# This defines who can perform which actions on which resources.
# Scriptdash uses CanCanCan for authorization.
#
# KEY CONCEPT: Permissions are role-based and defined per resource type
#
# Location: app/models/abilities/ability.rb (or wunderbar_ability.rb)

class Ability
  include CanCan::Ability

  def initialize(wunderbar_user)
    # PATTERN: Define abilities based on role
    if wunderbar_user&.ops?
      ops(wunderbar_user)
    elsif wunderbar_user&.manager?
      manager(wunderbar_user)
    elsif wunderbar_user&.sales?
      sales(wunderbar_user)
    # ... other roles
    end
  end

  # PATTERN: Role-specific abilities
  def ops(wunderbar_user = nil)
    # CRITICAL: Grant :read permission on Engine type (not Scriptdash type!)
    can :read, ActionsAPI::Types::V2::ActionPartnership

    # TODO: Add other permissions for ops role
    # can :create, ActionsAPI::Types::V2::ActionPartnership
    # can :update, ActionsAPI::Types::V2::ActionPartnership
    # can :manage, ActionsAPI::Types::V2::SomeOtherResource
  end

  def manager(wunderbar_user = nil)
    # Managers can only read, not create/update/delete
    can :read, ActionsAPI::Types::V2::ActionPartnership
  end

  def sales(wunderbar_user = nil)
    # Sales can read action partnerships
    can :read, ActionsAPI::Types::V2::ActionPartnership
  end

  # TODO: Define other role abilities
  # def engineer(wunderbar_user = nil)
  #   can :manage, :all  # Engineers can do anything
  # end
end

# PERMISSION ACTIONS:
# - :read - FetchOne, FetchAll, FetchBy, Search
# - :create - Create
# - :update - Update
# - :destroy - Delete
# - :manage - All actions (shorthand for create/read/update/destroy)

# WHY ENGINE TYPES IN PERMISSIONS?
# Scriptdash checks permissions on Engine types because:
# 1. Scriptdash returns Engine types (type reuse)
# 2. Single source of truth (Engine owns the type)
# 3. Permissions apply to the resource, not the API layer
