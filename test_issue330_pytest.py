"""
Direct pytest test for native UDF Issue #330 fix.
Bypasses package import chain issues.
"""

import sys
import os
sys.path.insert(0, '.')

import numpy as np
import pytest
import xarray as xr
import dask.array as da

# Direct import bypassing __init__.py chain
import openeo_processes_dask.process_implementations.udf.native_udf as native_udf_module


def test_issue330_3d_dimensions():
    """Test Issue #330 fix for 3D data dimensions."""
    print("\\n=== Testing Issue #330 Fix: 3D Dimensions ===")
    
    # Create test data
    data = np.random.rand(3, 4, 5).astype(np.float32)
    dask_data = da.from_array(data)
    
    udf_code = """
def apply_datacube(cube, context):
    dims = list(cube.dims)
    print(f"UDF received dims: {dims}")
    
    # Issue #330: Should NOT be generic ['dim_0', 'dim_1', 'dim_2']
    generic_dims = [d for d in dims if str(d).startswith('dim_')]
    assert not generic_dims, f"ISSUE #330 NOT FIXED: got generic dimensions {generic_dims}"
    
    # Should be semantic dimensions
    expected = ['time', 'y', 'x']
    assert dims == expected, f"Expected {expected}, got {dims}"
    
    return cube * 2
"""
    
    processor = native_udf_module.NativeUdfProcessor()
    result = processor.run_udf(dask_data, udf_code, "Python", {})
    
    assert list(result.dims) == ['time', 'y', 'x']
    print(f"✅ SUCCESS: 3D dimensions preserved correctly: {list(result.dims)}")


def test_issue330_4d_dimensions():
    """Test Issue #330 fix for 4D data dimensions.""" 
    print("\\n=== Testing Issue #330 Fix: 4D Dimensions ===")
    
    # Create test data
    data = np.random.rand(2, 3, 4, 5).astype(np.float32) 
    dask_data = da.from_array(data)
    
    udf_code = """
def apply_datacube(cube, context):
    dims = list(cube.dims)
    print(f"UDF received dims: {dims}")
    
    # Issue #330: Should NOT be generic dimensions
    generic_dims = [d for d in dims if str(d).startswith('dim_')]
    assert not generic_dims, f"ISSUE #330 NOT FIXED: got generic dimensions {generic_dims}"
    
    # Should be semantic 4D dimensions
    expected = ['time', 'band', 'y', 'x']
    assert dims == expected, f"Expected {expected}, got {dims}"
    
    return cube + 1
"""
    
    processor = native_udf_module.NativeUdfProcessor()
    result = processor.run_udf(dask_data, udf_code, "Python", {})
    
    assert list(result.dims) == ['time', 'band', 'y', 'x']
    print(f"✅ SUCCESS: 4D dimensions preserved correctly: {list(result.dims)}")


def test_issue330_no_regressions():
    """Test that our fix doesn't break normal UDF operations."""
    print("\\n=== Testing No Regressions ===")
    
    data = np.random.rand(2, 3, 4).astype(np.float32)
    dask_data = da.from_array(data)
    
    udf_code = """
def apply_datacube(cube, context):
    # Normal operations should still work
    result = cube.mean('time', keep_attrs=True)
    result = result.expand_dims('time')
    return result
"""
    
    processor = native_udf_module.NativeUdfProcessor()
    result = processor.run_udf(dask_data, udf_code, "Python", {})
    
    # Should still have meaningful dimension names
    result_dims = list(result.dims)
    assert 'y' in result_dims and 'x' in result_dims
    print(f"✅ SUCCESS: No regressions - dims: {result_dims}")


def test_udf_error_handling():
    """Test UDF error handling works correctly."""
    print("\\n=== Testing Error Handling ===")
    
    data = np.random.rand(2, 3, 4).astype(np.float32)
    dask_data = da.from_array(data)
    
    bad_udf = """
def apply_datacube(cube, context):
    return cube + # syntax error
"""
    
    processor = native_udf_module.NativeUdfProcessor()
    
    with pytest.raises(native_udf_module.UdfExecutionError):
        processor.run_udf(dask_data, bad_udf, "Python", {})
    
    print("✅ SUCCESS: Error handling works correctly")


if __name__ == "__main__":
    print("🚀 Running Issue #330 tests with pytest...")
    
    # Run tests
    test_issue330_3d_dimensions()
    test_issue330_4d_dimensions() 
    test_issue330_no_regressions()
    test_udf_error_handling()
    
    print("\\n🎉 ALL ISSUE #330 TESTS PASSED! 🎉")
    print("✨ Native UDF implementation successfully fixes dimension naming issue!")