
import sys
import os
import unittest
from flask import Flask

# Add project root to path
sys.path.append(os.getcwd())

from src.core.logger import log

class TestRegionRefactoring(unittest.TestCase):
    def test_imports(self):
        log.info("Testing Region API imports...")
        
        try:
            from src.api.v1.region_controller import region_blueprint
            log.info("Region Blueprint imported successfully.")
        except ImportError as e:
            self.fail(f"Failed to import Region Blueprint: {e}")

        try:
            from src.api.schemas.region import BatchUpdateCityProvinceRequest, UpdateCityProvinceRequest
            log.info("Region Schemas imported successfully.")
        except ImportError as e:
             self.fail(f"Failed to import Region Schemas: {e}")


    def test_schema_validation(self):
        log.info("Testing Schema Validation logic...")
        from src.api.schemas.region import BatchUpdateCityProvinceRequest, UpdateCityProvinceRequest

        # Test valid batch request
        data = {
            "cities": [
                {"city_code": "1", "province_code": "100"},
                {"city_code": "2", "province_code": "200", "province_name": "Test"}
            ]
        }
        req = BatchUpdateCityProvinceRequest(**data)
        self.assertEqual(len(req.cities), 2)
        self.assertEqual(req.cities[1].province_name, "Test")

        # Test invalid batch request (missing cities)
        with self.assertRaises(ValueError):
            BatchUpdateCityProvinceRequest(**{})

        log.info("Schema Validation logic validated.")

if __name__ == '__main__':
    unittest.main()
