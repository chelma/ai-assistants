# Statistical Outliers

## Summary

**Outliers requiring investigation**: NONE (all explained by file size)

## Outlier Definition

Files with >37 lines changed (>2 standard deviations from mean of 5.89 lines/file)

## Top 10 Outliers

1. **app/services/prescriptions/commands.rb** - 189 lines
2. **spec/services/billing/auto/autobill_shipment_delivery_1_spec.rb** - 140 lines
3. **spec/services/billing/auto/autobill_shipment_delivery_2_spec.rb** - 137 lines
4. **app/services/analytics/v1/delivery_analytics.rb** - 137 lines
5. **spec/services/prescriptions/commands_spec.rb** - 108 lines
6. **spec/requests/wunderbar/procurement/purchase_orders_spec.rb** - 107 lines
7. **spec/services/procurement/workers/process_order_confirmation_edi_file_spec.rb** - 106 lines
8. **spec/services/patient_comms/topics/new_delivery_processed_spec.rb** - 96 lines
9. **spec/services/billing/auto/apply_billing_outcome_spec.rb** - 93 lines
10. **spec/services/inventory/wunderbar/v1/scan_to_location_endpoint_spec.rb** - 80 lines

## Analysis

### Pattern Observation
- **Service files** with high change counts are large files with many method calls
- **Spec files** with high change counts are integration tests with many factory bot calls
- All outliers show **perfectly symmetric changes** (insertions = deletions)

### File Size Correlation
Large files naturally have more hash literals to convert:
- Large service classes: Many method calls with hash arguments
- Integration specs: Many `FactoryBot.create` calls with hash options
- Analytics services: Many logger calls with hash contexts

### Security Assessment
No outliers show:
- Logic changes beyond syntax conversion
- Added functionality
- Suspicious patterns
- Credential leaks
- Malicious code

## Asymmetric Files (Special Case)

Only 3 files show asymmetric changes (insertions ≠ deletions):

1. **app/services/billing/troubleshoot/insurance/new_york_medicaid_reject.rb**
   - **Change**: -5 lines (orphaned sig + initialize removal)
   - **Explanation**: Removed redundant signature declaration
   - **Risk**: None - cleanup

2. **app/services/billing/troubleshoot/insurance/days_supply_below_plan_minimum.rb**
   - **Change**: -5 lines (orphaned sig + initialize removal)
   - **Explanation**: Removed redundant signature declaration
   - **Risk**: None - cleanup

3. **spec/services/scheduling/delivery_windows/policies/resolve_default_spec.rb**
   - **Change**: +1 line (formatting)
   - **Explanation**: Multi-line hash reformatting
   - **Risk**: None - formatting

## Conclusion

All statistical outliers are explained by file size and code structure. No security concerns identified.
