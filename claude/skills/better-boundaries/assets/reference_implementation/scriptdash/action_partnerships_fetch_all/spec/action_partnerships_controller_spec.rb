require 'rails_helper'

# PATTERN DEMONSTRATED: Scriptdash Controller Spec (Mock Engine, Test Permissions)
#
# KEY DIFFERENCES from Engine spec:
# - Uses controller test helpers (get :index), not RPC client
# - Mocks Engine API (don't test Engine business logic)
# - Tests permissions (with/without access)
# - Tests delegation to Engine
#
# Location: spec/requests/wunderbar/{domain}/v{version}/{resource}_controller_spec.rb

RSpec.describe Wunderbar::Actions::V1::ActionPartnershipsController, { type: :controller } do

  # PATTERN: Login user before each test
  before(:each) do
    @wunderbar_user = FactoryBot.create(:manager_wb_user)  # ← User with :read permission
    login_wunderbar_user(@wunderbar_user)
  end

  describe 'GET /actions/v1/action_partnerships/fetch_all' do

    # PATTERN: Mock Engine API response (don't call real Engine)
    let(:mock_action_partnerships) do
      [
        ActionsAPI::Types::V2::ActionPartnership.new(
          id: 1,
          name: 'Progyny',
          value: 'progyny',
        ),
        ActionsAPI::Types::V2::ActionPartnership.new(
          id: 2,
          name: 'Carrot',
          value: 'carrot',
        ),
        ActionsAPI::Types::V2::ActionPartnership.new(
          id: 3,
          name: 'Iterum',
          value: 'iterum',
        ),
      ]
    end

    before do
      # CRITICAL: Mock Engine API (isolate Scriptdash tests from Engine)
      allow(Actions.action_partnerships).to receive(:fetch_all)
        .and_return(mock_action_partnerships)
    end

    it 'returns all action partnerships successfully' do
      get :index  # ← Use controller test helper (not client.fetch_all)

      # Verify HTTP response
      expect(response).to have_http_status(200)

      # Verify response body (JSON)
      body = JSON.parse(response.body)
      expect(body['data']).to be_an(Array)
      expect(body['data'].length).to eq(3)
      expect(body['data'].first['name']).to eq('Progyny')
      expect(body['data'].first['value']).to eq('progyny')
    end

    it 'calls Engine API' do
      # PATTERN: Verify delegation to Engine
      expect(Actions.action_partnerships).to receive(:fetch_all)
        .and_return(mock_action_partnerships)

      get :index
    end

    # PATTERN: Test permissions (unauthorized scenarios)
    context 'without permission' do
      before do
        # Create user without :read permission
        @wunderbar_user = FactoryBot.create(:basic_wb_user)  # ← No permissions
        login_wunderbar_user(@wunderbar_user)
      end

      it 'returns unauthorized' do
        # CRITICAL: Verify CanCan::AccessDenied raised
        expect { get :index }.to raise_error(CanCan::AccessDenied)
      end
    end

    # TODO: Test error handling
    # context 'when Engine returns error' do
    #   before do
    #     allow(Actions.action_partnerships).to receive(:fetch_all)
    #       .and_raise(StandardError.new('Engine error'))
    #   end
    #
    #   it 'returns error response' do
    #     expect { get :index }.to raise_error(StandardError)
    #   end
    # end
  end
end

# KEY TESTING PRINCIPLES:
# 1. Mock Engine API - don't test Engine business logic here
# 2. Test permissions - ensure unauthorized users are blocked
# 3. Test delegation - verify Engine API is called correctly
# 4. Test response format - ensure JSON structure is correct
# 5. Use controller helpers - get :index, not client.fetch_all
