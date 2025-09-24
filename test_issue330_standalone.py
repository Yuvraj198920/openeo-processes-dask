"""
Standalone pytest test for Issue #330 fix.
This test validates our native UDF implementation without full package dependencies.
"""

import numpy as np
import pytest
import xarray as xr
import dask.array as da
import sys
import os

# Add the package root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Direct import of our native UDF module to avoid circular dependencies
from openeo_processes_dask.process_implementations.udf.native_udf import (
    NativeUdfProcessor,
    UdfExecutionError
)


class TestIssue330Fix:
    """Test class for Issue #330 dimension preservation fix."""
    
    def test_3d_semantic_dimensions_preserved(self):
        """Test that 3D data preserves semantic dimension names (time, y, x)."""
        # Create 3D test data
        data = np.random.rand(3, 4, 5).astype(np.float32)
        dask_data = da.from_array(data)
        
        udf_code = """
def apply_datacube(cube, context):
    # Verify we get semantic dimensions, not dim_0, dim_1, dim_2
    dims = list(cube.dims)
    assert 'time' in dims, f"Expected 'time' in dimensions, got {dims}"
    assert 'y' in dims, f"Expected 'y' in dimensions, got {dims}"
    assert 'x' in dims, f"Expected 'x' in dimensions, got {dims}"
    # Issue #330 check: no generic dimensions
    generic_dims = [d for d in dims if str(d).startswith('dim_')]
    assert not generic_dims, f"Issue #330 regression: found generic dimensions {generic_dims}"
    return cube * 2
"""
        
        processor = NativeUdfProcessor()
        result = processor.run_udf(dask_data, udf_code, "Python", {})
        
        # Validate result dimensions
        assert list(result.dims) == ['time', 'y', 'x']
        print(f"✅ 3D test PASSED - dimensions: {list(result.dims)}")
    
    def test_4d_semantic_dimensions_preserved(self):
        """Test that 4D data preserves semantic dimension names (time, band, y, x)."""
        # Create 4D test data
        data = np.random.rand(2, 3, 4, 5).astype(np.float32)
        dask_data = da.from_array(data)
        
        udf_code = """
def apply_datacube(cube, context):
    dims = list(cube.dims)
    expected = ['time', 'band', 'y', 'x']
    assert dims == expected, f"Expected {expected}, got {dims}"
    # Issue #330 check: no generic dimensions
    generic_dims = [d for d in dims if str(d).startswith('dim_')]
    assert not generic_dims, f"Issue #330 regression: found generic dimensions {generic_dims}"
    return cube + 1
"""
        
        processor = NativeUdfProcessor()
        result = processor.run_udf(dask_data, udf_code, "Python", {})
        
        # Validate result dimensions  
        assert list(result.dims) == ['time', 'band', 'y', 'x']
        print(f"✅ 4D test PASSED - dimensions: {list(result.dims)}")
    
    def test_dimension_consistency(self):
        """Test that dimensions remain consistent through UDF operations."""
        data = np.random.rand(2, 3, 4).astype(np.float32)
        dask_data = da.from_array(data)
        
        udf_code = """
def apply_datacube(cube, context):
    # Complex operations that should preserve dimensions
    result = cube.mean('time').expand_dims('time')
    # Check dimensions are still semantic
    dims = list(result.dims)
    assert 'y' in dims and 'x' in dims, f"Lost spatial dimensions: {dims}"
    return result
"""
        
        processor = NativeUdfProcessor()
        result = processor.run_udf(dask_data, udf_code, "Python", {})
        
        # Should have preserved spatial dimensions
        result_dims = list(result.dims)
        assert 'y' in result_dims
        assert 'x' in result_dims
        print(f"✅ Consistency test PASSED - dimensions: {result_dims}")

    def test_error_handling(self):
        """Test that UDF errors are properly handled."""
        data = np.random.rand(2, 3, 4).astype(np.float32)
        dask_data = da.from_array(data)
        
        # UDF with syntax error
        bad_udf = """
def apply_datacube(cube, context):
    return cube + # syntax error
"""
        
        processor = NativeUdfProcessor()
        with pytest.raises(UdfExecutionError):
            processor.run_udf(dask_data, bad_udf, "Python", {})
        
        print("✅ Error handling test PASSED")


def test_issue330_integration():
    """Integration test reproducing the original Issue #330 scenario."""
    print("\\n=== Issue #330 Integration Test ===")
    
    # Test 3D data (original issue case)
    data_3d = np.random.rand(5, 10, 10).astype(np.float32)
    dask_data_3d = da.from_array(data_3d)
    
    udf_code = """
def apply_datacube(cube, context):
    print(f"UDF received dims: {list(cube.dims)}")
    dims = list(cube.dims)
    # The fix: should NOT be ['dim_0', 'dim_1', 'dim_2']
    generic_dims = [d for d in dims if str(d).startswith('dim_')]
    if generic_dims:
        raise ValueError(f"Issue #330 NOT FIXED: got generic dims {generic_dims}")
    # Should be semantic dimensions
    expected_semantic = ['time', 'y', 'x'] 
    if dims != expected_semantic:
        raise ValueError(f"Expected {expected_semantic}, got {dims}")
    return cube.mean('time')
"""
    
    processor = NativeUdfProcessor()
    result = processor.run_udf(dask_data_3d, udf_code, "Python", {})
    print(f"✅ Issue #330 Integration PASSED - final dims: {list(result.dims)}")


if __name__ == "__main__":
    print("Running Issue #330 tests with pytest...")
    
    # Run the tests
    test_class = TestIssue330Fix()
    test_class.test_3d_semantic_dimensions_preserved()
    test_class.test_4d_semantic_dimensions_preserved() 
    test_class.test_dimension_consistency()
    test_class.test_error_handling()
    
    test_issue330_integration()
    
    print("\\n🎉 All Issue #330 tests PASSED! 🎉")