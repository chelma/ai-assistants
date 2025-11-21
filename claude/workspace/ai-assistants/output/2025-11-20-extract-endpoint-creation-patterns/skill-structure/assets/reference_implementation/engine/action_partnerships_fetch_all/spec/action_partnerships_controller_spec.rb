require 'rails_helper'

# PATTERN DEMONSTRATED: Engine Request Spec (Full-Stack Test)
#
# Tests the complete stack: HTTP → Controller → Endpoint → Database → Response
# Uses RPC client to test like a real consumer would call the API.
#
# KEY CONCEPT: Test via RPC client (not controller directly) for realistic testing
#
# Location: spec/requests/{domain}_engine/v{version}/{resource}_controller_spec.rb

RSpec.describe ActionsEngine::V2::ActionPartnershipsController,
               :rpc_client_requests,  # ← CRITICAL: Enables RPC testing helpers
               type: :request do

  # PATTERN: Use RPC client (not HTTP helpers) to test
  let(:client) { ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient.new }

  describe 'GET /v2/action_partnerships/fetch_all' do
    subject(:fetch_all) do
      client.fetch_all  # ← Calls RPC method (internally makes HTTP GET request)
    end

    context 'with action partnerships' do
      before do
        # PATTERN: Use factories to create test data
        create(:action_partnership, name: 'Progyny', value: 'progyny', company_id: 1)
        create(:action_partnership, name: 'Carrot', value: 'carrot', company_id: 1)
      end

      it 'returns all action partnerships' do
        result = fetch_all

        # PATTERN: Verify response structure and types
        expect(result).to be_an(Array)
        expect(result.length).to eq(2)
        expect(result.first).to be_a(ActionsAPI::Types::V2::ActionPartnership)

        # PATTERN: Verify data content
        expect(result.first.name).to eq('Progyny')
        expect(result.first.value).to eq('progyny')
      end
    end

    context 'with no action partnerships' do
      it 'returns empty array' do
        result = fetch_all
        expect(result).to eq([])
      end
    end

    # TODO: Add error cases
    # context 'when database error occurs' do
    #   before do
    #     allow(ActionPartnership).to receive(:all).and_raise(ActiveRecord::ConnectionNotEstablished)
    #   end
    #
    #   it 'returns error response' do
    #     expect { fetch_all }.to raise_error(...)
    #   end
    # end
  end
end

# KEY DIFFERENCES from standard controller specs:
# 1. Use RPC client, not `get :index` or `get '/v2/action_partnerships/fetch_all'`
# 2. No need to parse JSON - client returns typed structs
# 3. Tests full stack including serialization/deserialization
# 4. Matches how real consumers will call the API
