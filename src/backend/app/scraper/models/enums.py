from enum import Enum

class Table(str, Enum):
    rtpi_price = "rtpi_price"
    rtpi_price_page = "rtpi_price_page"
    rtpi_product_name = "rtpi_product_name"
    rtpi_store_id = "rtpi_store_id"