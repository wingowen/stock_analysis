# Simple test script to verify code structure

# Test 1: Import the data sources module
try:
    from data_sources import StockDataSourceFactory
    print("✓ Successfully imported StockDataSourceFactory")
except Exception as e:
    print(f"✗ Failed to import StockDataSourceFactory: {e}")

# Test 2: Create a data source factory
try:
    factory = StockDataSourceFactory()
    print("✓ Successfully created StockDataSourceFactory instance")
except Exception as e:
    print(f"✗ Failed to create StockDataSourceFactory instance: {e}")

# Test 3: Test Sina Finance data source creation
try:
    data_source = StockDataSourceFactory.create_data_source("sina_finance")
    if data_source:
        print("✓ Successfully created Sina Finance data source")
        print(f"  - Source name: {data_source.source_name}")
    else:
        print("✗ Failed to create Sina Finance data source")
except Exception as e:
    print(f"✗ Error creating Sina Finance data source: {e}")

# Test 4: Test East Money data source creation
try:
    data_source = StockDataSourceFactory.create_data_source("eastmoney")
    if data_source:
        print("✓ Successfully created East Money data source")
        print(f"  - Source name: {data_source.source_name}")
    else:
        print("✗ Failed to create East Money data source")
except Exception as e:
    print(f"✗ Error creating East Money data source: {e}")

# Test 5: Test unknown data source creation
try:
    data_source = StockDataSourceFactory.create_data_source("unknown")
    if data_source is None:
        print("✓ Correctly returned None for unknown data source")
    else:
        print("✗ Should have returned None for unknown data source")
except Exception as e:
    print(f"✗ Error creating unknown data source: {e}")

print("\nAll tests completed!")
