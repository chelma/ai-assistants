# FetchAll/FetchOne Endpoint Patterns - Quick Reference Guide

## By the Numbers

| Metric | Count |
|--------|-------|
| Proto files with FetchAll | 39 |
| Proto files with FetchOne | 25 |
| Ruby endpoints with fetch_all | 56 |
| Ruby endpoints with fetch_one | 44 |
| Endpoints with BOTH methods | 16 |
| Total domains covered | 24 |

## Proto Pattern Templates

### FetchAll - Simple (No Parameters)
```proto
message Request {}
message Response {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated DataType data = 2;
}
rpc FetchAll(Request) returns (Response);
```

### FetchAll - Batch (ID Array)
```proto
message Request {
  repeated int64 ids = 1 [(opts.field) = {required: true}];
}
message Response {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated DataType data = 2;
}
rpc FetchAll(Request) returns (Response);
```

### FetchAll - Paginated
```proto
message Request {
  int64 context_id = 1 [(opts.field) = {required: true}];
  core.types.v1.PaginationRequestParams pagination = 2;
}
message ResponseMetadata {
  core.types.v1.PaginationResponseMetadata pagination = 1;
}
message Response {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated DataType data = 2;
  ResponseMetadata metadata = 3;
}
rpc FetchAll(Request) returns (Response);
```

### FetchOne - Standard
```proto
message Request {
  int64 id = 1 [(opts.field) = {required: true}];
}
message Response {
  repeated core.types.v1.ErrorObject errors = 1;
  DataType data = 2;  // Singular!
}
rpc FetchOne(Request) returns (Response);
```

## Ruby Pattern Templates

### FetchAll - Simple
```ruby
def fetch_all
  current_ability.authorize! :read, MyType
  MyService.fetch_all
end
```

### FetchAll - Batch
```ruby
def fetch_all(ids:)
  MyModel.find(ids).map { |m| to_struct(m) }
end
```

### FetchAll - Paginated
```ruby
def fetch_all(parent_id:, page_size: nil, page_token: nil)
  current_ability.authorize! :read, MyModel
  
  response = MyService.fetch_by_parent(
    parent_id: parent_id,
    page_size: page_size,
    page_token: page_token
  )
  
  I::MyEndpointFetchAllResponse.new({
    data: response.data,
    errors: response.errors,
    metadata: I::ResponseMetadata.new(
      pagination: response.metadata.pagination
    )
  })
end
```

### FetchOne - Direct Lookup
```ruby
def fetch_one(id:)
  current_ability.authorize! :read, MyType
  MyService.fetch_one(id:)
end
```

### FetchOne - With Error Handling
```ruby
def fetch_one(id:)
  result = MyService.find_by_id(id)
  raise Core::Error::NotFoundError, "Not found" if result.nil?
  to_struct(result)
end
```

### FetchOne - With Access Control
```ruby
def fetch_one(id:)
  current_ability.authorize! :read, MyModel
  record = MyService.fetch_one(id:)
  
  if @current_user.cannot_access?(record)
    raise Core::Error::AltoError, "Access denied"
  end
  
  record
end
```

## Authorization Patterns

### Via Mixin
```ruby
include Auth::CurrentAbility

def fetch_all
  current_ability.authorize! :read, MyType
  # ...
end
```

### Via Constructor
```ruby
def initialize(ability:)
  @ability = ability
end

def fetch_all
  @ability.authorize! :read, MyType
  # ...
end
```

### Via Current User
```ruby
def initialize(current_user)
  @current_user = current_user
end

def fetch_one(id:)
  current_ability.authorize! :read, ::User.new(id: id)
  # ...
end
```

## Response Structure

### FetchAll Response
```json
{
  "errors": null,
  "data": [
    { "id": 1, "name": "Item 1" },
    { "id": 2, "name": "Item 2" }
  ],
  "metadata": {
    "pagination": {
      "page_size": 50,
      "page_token": "0",
      "total_count": 123
    }
  }
}
```

### FetchOne Response
```json
{
  "errors": null,
  "data": {
    "id": 1,
    "name": "Item 1"
  }
}
```

### Error Response
```json
{
  "errors": [
    {
      "code": "NOT_FOUND",
      "detail": "Record not found",
      "title": "Not Found"
    }
  ],
  "data": null
}
```

## Common Implementation Patterns

### Pattern 1: Delegation to Core API
```ruby
# Simple pass-through
def fetch_one(id:)
  Actions.action_types.v2.fetch_one(id:)
end
```

### Pattern 2: Direct Model Query + Struct Mapping
```ruby
def fetch_all(ids:)
  MyModel.find(ids).map { |m| to_struct(m) }
end

private

sig { params(model: ::MyModel).returns(TYPES::MyType) }
def to_struct(model)
  TYPES::MyType.new(
    id: model.id,
    name: model.name
  )
end
```

### Pattern 3: Service Layer
```ruby
def fetch_all(patient_id:)
  response = MyService.fetch_by_patient(patient_id:)
  
  ResponseType.new(
    data: response.data,
    errors: response.errors
  )
end
```

## Common Parameter Names

### FetchAll Parameters
- `ids` - For batch fetch by ID array
- `{parent}_id` - For contextual fetch (patient_id, user_id)
- `page_size` - Pagination: items per page
- `page_token` - Pagination: offset or cursor
- `is_internal` - Boolean filter flag
- `filters` - Complex filtering object

### FetchOne Parameters
- `id` - Standard primary key
- `{type}_identifier` - Domain-specific identifier

## Testing Patterns

### FetchAll Test
```ruby
describe 'fetch all' do
  it 'returns items for the given parent' do
    get('/api/items', params: { patient_id: 123 })
    
    expect(response).to have_http_status(:success)
    result = JSON.parse(response.body)['data']
    expect(result.length).to eq(2)
  end
end
```

### FetchOne Test
```ruby
describe 'fetch one' do
  it 'returns the item' do
    get("/api/items/#{item.id}")
    
    expect(response).to have_http_status(:success)
    result = JSON.parse(response.body)['data']
    expect(result['id']).to eq(item.id)
  end
  
  it 'returns 404 for missing item' do
    get('/api/items/999999')
    
    expect(response).to have_http_status(:not_found)
  end
end
```

## Best Practices Checklist

- [ ] Proto definitions first, before Ruby code
- [ ] Both FetchAll and FetchOne for collection endpoints
- [ ] Authorization check in every endpoint
- [ ] Use Sorbet type signatures
- [ ] Map models to structs before returning
- [ ] Include pagination for large datasets
- [ ] Test authorization failures
- [ ] Test not-found cases
- [ ] Use Core API services when available
- [ ] Consistent error format across endpoints

## Domains Quick Lookup

**Customer Support Heavy (7+ endpoints)**
- support_cases, support_categories, notifications, chatbot_sessions, wundercom_messages

**Billing (4 endpoints)**
- prices, voucher_payers, insurances

**Providers (5+ endpoints)**
- agency_agreements, tia_templates, viewable_clinics, viewable_providers

**Actions (5 endpoints)**
- action_partnerships, action_pods, action_type_configs, aspect_roles, task_thresholds

**Patient App (5+ endpoints)**
- availability_options, facility_alert, fee_configs, opt_outs, instructional_videos

## File Locations

### Protos
```
protos/src/<domain>/<subdomain>/<version>/<endpoint>_endpoint.proto
```

### Ruby Implementations
```
app/services/<domain>/<subdomain>/<version>/<endpoint>_endpoint.rb
```

### Routes
```
config/routes.rb
config/routes/providers.rb
```

### Tests
```
spec/requests/<context>/<endpoint>_spec.rb
spec/services/<domain>/<endpoint>_spec.rb
```

