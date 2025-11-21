# PATTERN DEMONSTRATED: Testing Intermediate Pattern Endpoint
# LOCATION: scriptdash/spec/requests/operations/v1/wunderbar_users_endpoint_spec.rb
# KEY CONCEPT: Test via engine routes, implementation runs in Scriptdash

require 'rails_helper'

# CRITICAL: Test using engine's controller path
RSpec.describe 'Operations::V1::WunderbarUsersEndpoint', type: :request do
  # PATTERN: Create test data using Scriptdash factories/models
  let!(:user1) do
    WunderbarUser.create!(
      email: 'alice@example.com',
      first_name: 'Alice',
      last_name: 'Anderson',
      team: 'Engineering',
      pod: 'backend',
    )
  end

  let!(:user2) do
    WunderbarUser.create!(
      email: 'bob@example.com',
      first_name: 'Bob',
      last_name: 'Brown',
      team: 'Operations',
      pod: 'ops',
    )
  end

  # PATTERN: Test FetchOne via engine route
  describe 'GET /v1/wunderbar_users/:id' do
    it 'returns the wunderbar user' do
      # CRITICAL: Route provided by engine, implementation in Scriptdash
      get "/v1/wunderbar_users/#{user1.id}"

      expect(response).to have_http_status(200)
      body = JSON.parse(response.body)

      # Verify response structure (from proto)
      expect(body['data']).to be_present
      expect(body['data']['id']).to eq(user1.id)
      expect(body['data']['email']).to eq('alice@example.com')
      expect(body['data']['first_name']).to eq('Alice')
      expect(body['data']['full_name']).to eq('Alice Anderson')
    end

    context 'when user does not exist' do
      it 'returns 404' do
        get '/v1/wunderbar_users/99999'

        expect(response).to have_http_status(404)
      end
    end
  end

  # PATTERN: Test FetchAll via engine route
  describe 'GET /v1/wunderbar_users' do
    context 'without IDs (fetch all)' do
      it 'returns all wunderbar users' do
        get '/v1/wunderbar_users'

        expect(response).to have_http_status(200)
        body = JSON.parse(response.body)

        expect(body['data']).to be_an(Array)
        expect(body['data'].length).to eq(2)

        # Verify both users present
        emails = body['data'].map { |u| u['email'] }
        expect(emails).to contain_exactly('alice@example.com', 'bob@example.com')
      end
    end

    context 'with IDs filter' do
      it 'returns only specified users' do
        get "/v1/wunderbar_users?ids[]=#{user1.id}"

        expect(response).to have_http_status(200)
        body = JSON.parse(response.body)

        expect(body['data'].length).to eq(1)
        expect(body['data'][0]['email']).to eq('alice@example.com')
      end
    end
  end
end

# KEY DIFFERENCES from Engine-only tests:
# - No RPC client (testing as regular Rails request)
# - No :rpc_client_requests helper needed
# - Uses Scriptdash models/factories directly
# - Routes are engine routes (/v1/...) not Scriptdash routes (/operations/v1/...)
