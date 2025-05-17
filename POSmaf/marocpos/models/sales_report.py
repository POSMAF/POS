from database import get_connection
from datetime import datetime, timedelta
import json
import sqlite3

class SalesReport:
    """Class to generate and manage sales reports"""
    
    @staticmethod
    def get_daily_sales(date=None):
        """Get sales data for a specific date, defaults to today"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Format the date strings for comparison
                start_date = f"{date} 00:00:00"
                end_date = f"{date} 23:59:59"
                
                # Get total sales data
                cursor.execute("""
                    SELECT 
                        COUNT(*) as sale_count,
                        SUM(final_total) as total_sales,
                        AVG(final_total) as average_sale,
                        MIN(final_total) as min_sale,
                        MAX(final_total) as max_sale,
                        SUM(discount) as total_discount
                    FROM Sales
                    WHERE created_at BETWEEN ? AND ?
                """, (start_date, end_date))
                
                summary = dict(cursor.fetchone() or {})
                
                # Get sales by hour
                cursor.execute("""
                    SELECT 
                        strftime('%H', created_at) as hour,
                        COUNT(*) as sale_count,
                        SUM(final_total) as total_sales
                    FROM Sales
                    WHERE created_at BETWEEN ? AND ?
                    GROUP BY hour
                    ORDER BY hour
                """, (start_date, end_date))
                
                hourly_sales = [dict(row) for row in cursor.fetchall()]
                
                # Get sales by payment method
                cursor.execute("""
                    SELECT 
                        COALESCE(pm.name, s.payment_method) as payment_method,
                        COUNT(DISTINCT s.id) as sale_count,
                        SUM(COALESCE(sp.amount, s.final_total)) as total_amount
                    FROM Sales s
                    LEFT JOIN SalePayments sp ON s.id = sp.sale_id
                    LEFT JOIN PaymentMethods pm ON sp.payment_method_id = pm.id
                    WHERE s.created_at BETWEEN ? AND ?
                    GROUP BY payment_method
                    ORDER BY total_amount DESC
                """, (start_date, end_date))
                
                payment_methods = [dict(row) for row in cursor.fetchall()]
                
                # Top selling products
                cursor.execute("""
                    SELECT 
                        p.id as product_id,
                        p.name as product_name,
                        SUM(si.quantity) as quantity_sold,
                        SUM(si.subtotal) as total_sales,
                        COUNT(DISTINCT s.id) as number_of_sales
                    FROM SaleItems si
                    JOIN Sales s ON si.sale_id = s.id
                    JOIN Products p ON si.product_id = p.id
                    WHERE s.created_at BETWEEN ? AND ?
                    GROUP BY p.id
                    ORDER BY quantity_sold DESC
                    LIMIT 10
                """, (start_date, end_date))
                
                top_products = [dict(row) for row in cursor.fetchall()]
                
                # Top selling categories
                cursor.execute("""
                    SELECT 
                        COALESCE(c.name, 'Non catégorisé') as category_name,
                        COUNT(DISTINCT si.id) as items_sold,
                        SUM(si.subtotal) as total_sales
                    FROM SaleItems si
                    JOIN Sales s ON si.sale_id = s.id
                    JOIN Products p ON si.product_id = p.id
                    LEFT JOIN Categories c ON p.category_id = c.id
                    WHERE s.created_at BETWEEN ? AND ?
                    GROUP BY COALESCE(c.name, 'Non catégorisé')
                    ORDER BY total_sales DESC
                """, (start_date, end_date))
                
                top_categories = [dict(row) for row in cursor.fetchall()]
                
                result = {
                    'date': date,
                    'summary': summary,
                    'hourly_sales': hourly_sales,
                    'payment_methods': payment_methods,
                    'top_products': top_products,
                    'top_categories': top_categories
                }
                
                return result
            except Exception as e:
                print(f"Error getting daily sales: {e}")
                return None
            finally:
                conn.close()
        return None
    
    @staticmethod
    def get_sales_range(start_date, end_date):
        """Get sales data for a date range"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Format the date strings for comparison if they're not already formatted
                if not start_date.endswith('00:00:00'):
                    start_date = f"{start_date} 00:00:00"
                if not end_date.endswith('23:59:59'):
                    end_date = f"{end_date} 23:59:59"
                
                # Get total sales data
                cursor.execute("""
                    SELECT 
                        COUNT(*) as sale_count,
                        SUM(final_total) as total_sales,
                        AVG(final_total) as average_sale,
                        MIN(final_total) as min_sale,
                        MAX(final_total) as max_sale,
                        SUM(discount) as total_discount
                    FROM Sales
                    WHERE created_at BETWEEN ? AND ?
                """, (start_date, end_date))
                
                summary = dict(cursor.fetchone() or {})
                
                # Get sales by day
                cursor.execute("""
                    SELECT 
                        date(created_at) as day,
                        COUNT(*) as sale_count,
                        SUM(final_total) as total_sales
                    FROM Sales
                    WHERE created_at BETWEEN ? AND ?
                    GROUP BY day
                    ORDER BY day
                """, (start_date, end_date))
                
                daily_sales = [dict(row) for row in cursor.fetchall()]
                
                # Get sales by payment method
                cursor.execute("""
                    SELECT 
                        COALESCE(pm.name, s.payment_method) as payment_method,
                        COUNT(DISTINCT s.id) as sale_count,
                        SUM(COALESCE(sp.amount, s.final_total)) as total_amount
                    FROM Sales s
                    LEFT JOIN SalePayments sp ON s.id = sp.sale_id
                    LEFT JOIN PaymentMethods pm ON sp.payment_method_id = pm.id
                    WHERE s.created_at BETWEEN ? AND ?
                    GROUP BY payment_method
                    ORDER BY total_amount DESC
                """, (start_date, end_date))
                
                payment_methods = [dict(row) for row in cursor.fetchall()]
                
                # Top selling products
                cursor.execute("""
                    SELECT 
                        p.id as product_id,
                        p.name as product_name,
                        SUM(si.quantity) as quantity_sold,
                        SUM(si.subtotal) as total_sales,
                        COUNT(DISTINCT s.id) as number_of_sales
                    FROM SaleItems si
                    JOIN Sales s ON si.sale_id = s.id
                    JOIN Products p ON si.product_id = p.id
                    WHERE s.created_at BETWEEN ? AND ?
                    GROUP BY p.id
                    ORDER BY quantity_sold DESC
                    LIMIT 20
                """, (start_date, end_date))
                
                top_products = [dict(row) for row in cursor.fetchall()]
                
                # Top selling categories
                cursor.execute("""
                    SELECT 
                        COALESCE(c.name, 'Non catégorisé') as category_name,
                        COUNT(DISTINCT si.id) as items_sold,
                        SUM(si.subtotal) as total_sales
                    FROM SaleItems si
                    JOIN Sales s ON si.sale_id = s.id
                    JOIN Products p ON si.product_id = p.id
                    LEFT JOIN Categories c ON p.category_id = c.id
                    WHERE s.created_at BETWEEN ? AND ?
                    GROUP BY COALESCE(c.name, 'Non catégorisé')
                    ORDER BY total_sales DESC
                """, (start_date, end_date))
                
                top_categories = [dict(row) for row in cursor.fetchall()]
                
                # Get sales by user
                cursor.execute("""
                    SELECT 
                        u.username as user,
                        COUNT(s.id) as sale_count,
                        SUM(s.final_total) as total_sales
                    FROM Sales s
                    JOIN Users u ON s.user_id = u.id
                    WHERE s.created_at BETWEEN ? AND ?
                    GROUP BY u.username
                    ORDER BY total_sales DESC
                """, (start_date, end_date))
                
                sales_by_user = [dict(row) for row in cursor.fetchall()]
                
                result = {
                    'start_date': start_date.split()[0],
                    'end_date': end_date.split()[0],
                    'summary': summary,
                    'daily_sales': daily_sales,
                    'payment_methods': payment_methods,
                    'top_products': top_products,
                    'top_categories': top_categories,
                    'sales_by_user': sales_by_user
                }
                
                return result
            except Exception as e:
                print(f"Error getting sales range: {e}")
                return None
            finally:
                conn.close()
        return None
    
    @staticmethod
    def get_product_performance(product_id, start_date=None, end_date=None):
        """Get sales performance data for a specific product"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        p.id as product_id,
                        p.name as product_name,
                        p.unit_price as current_price,
                        p.purchase_price as current_cost,
                        SUM(si.quantity) as total_quantity,
                        SUM(si.subtotal) as total_sales,
                        COUNT(DISTINCT s.id) as number_of_sales,
                        AVG(si.unit_price) as average_price,
                        date(MIN(s.created_at)) as first_sold,
                        date(MAX(s.created_at)) as last_sold
                    FROM SaleItems si
                    JOIN Sales s ON si.sale_id = s.id
                    JOIN Products p ON si.product_id = p.id
                    WHERE si.product_id = ?
                """
                
                params = [product_id]
                
                if start_date:
                    query += " AND s.created_at >= ?"
                    params.append(f"{start_date} 00:00:00")
                    
                if end_date:
                    query += " AND s.created_at <= ?"
                    params.append(f"{end_date} 23:59:59")
                    
                query += " GROUP BY p.id"
                
                cursor.execute(query, params)
                product_summary = dict(cursor.fetchone() or {})
                
                # Get sales by month
                query = """
                    SELECT 
                        strftime('%Y-%m', s.created_at) as month,
                        SUM(si.quantity) as quantity_sold,
                        SUM(si.subtotal) as total_sales,
                        COUNT(DISTINCT s.id) as number_of_sales
                    FROM SaleItems si
                    JOIN Sales s ON si.sale_id = s.id
                    WHERE si.product_id = ?
                """
                
                params = [product_id]
                
                if start_date:
                    query += " AND s.created_at >= ?"
                    params.append(f"{start_date} 00:00:00")
                    
                if end_date:
                    query += " AND s.created_at <= ?"
                    params.append(f"{end_date} 23:59:59")
                    
                query += " GROUP BY month ORDER BY month"
                
                cursor.execute(query, params)
                monthly_sales = [dict(row) for row in cursor.fetchall()]
                
                # Get variant sales if product has variants
                cursor.execute("""
                    SELECT has_variants FROM Products WHERE id = ?
                """, (product_id,))
                
                has_variants = cursor.fetchone()
                variant_sales = []
                
                if has_variants and has_variants[0]:
                    query = """
                        SELECT 
                            si.variant_id,
                            pv.attribute_values,
                            SUM(si.quantity) as quantity_sold,
                            SUM(si.subtotal) as total_sales,
                            COUNT(DISTINCT s.id) as number_of_sales
                        FROM SaleItems si
                        JOIN Sales s ON si.sale_id = s.id
                        JOIN ProductVariants pv ON si.variant_id = pv.id
                        WHERE si.product_id = ? AND si.variant_id IS NOT NULL
                    """
                    
                    params = [product_id]
                    
                    if start_date:
                        query += " AND s.created_at >= ?"
                        params.append(f"{start_date} 00:00:00")
                        
                    if end_date:
                        query += " AND s.created_at <= ?"
                        params.append(f"{end_date} 23:59:59")
                        
                    query += " GROUP BY si.variant_id ORDER BY quantity_sold DESC"
                    
                    cursor.execute(query, params)
                    variant_rows = cursor.fetchall()
                    
                    for row in variant_rows:
                        variant_data = dict(row)
                        
                        # Parse attribute_values
                        try:
                            if variant_data['attribute_values']:
                                if isinstance(variant_data['attribute_values'], str):
                                    variant_data['attributes'] = json.loads(variant_data['attribute_values'])
                                else:
                                    variant_data['attributes'] = variant_data['attribute_values']
                                    
                                # Create a display name for the variant
                                if isinstance(variant_data['attributes'], dict):
                                    variant_data['variant_name'] = " / ".join(str(v) for v in variant_data['attributes'].values() if v)
                                else:
                                    variant_data['variant_name'] = f"Variant #{variant_data['variant_id']}"
                        except:
                            variant_data['attributes'] = {}
                            variant_data['variant_name'] = f"Variant #{variant_data['variant_id']}"
                            
                        variant_sales.append(variant_data)
                
                return {
                    'product': product_summary,
                    'monthly_sales': monthly_sales,
                    'variant_sales': variant_sales
                }
            except Exception as e:
                print(f"Error getting product performance: {e}")
                return None
            finally:
                conn.close()
        return None
    
    @staticmethod
    def get_inventory_report():
        """Get inventory status report for all products"""
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Get inventory status for regular products
                cursor.execute("""
                    SELECT 
                        p.id as product_id,
                        p.name as product_name,
                        COALESCE(c.name, 'Non catégorisé') as category_name,
                        p.stock as current_stock,
                        p.min_stock as minimum_stock,
                        p.reorder_point as reorder_point,
                        p.purchase_price as cost,
                        p.unit_price as price,
                        p.has_variants,
                        CASE 
                            WHEN p.stock <= p.min_stock THEN 'low'
                            WHEN p.stock <= p.reorder_point THEN 'warning'
                            ELSE 'ok'
                        END as stock_status,
                        p.purchase_price * p.stock as stock_value,
                        p.unit_price * p.stock as retail_value
                    FROM Products p
                    LEFT JOIN Categories c ON p.category_id = c.id
                    ORDER BY stock_status, p.name
                """)
                
                products = [dict(row) for row in cursor.fetchall()]
                
                # Get inventory status for variants
                cursor.execute("""
                    SELECT 
                        pv.id as variant_id,
                        p.id as product_id,
                        p.name as product_name,
                        pv.attribute_values,
                        pv.stock as current_stock,
                        pv.price_adjustment,
                        COALESCE(p.purchase_price, 0) as base_cost,
                        COALESCE(p.unit_price, 0) as base_price,
                        COALESCE(p.unit_price, 0) + COALESCE(pv.price_adjustment, 0) as variant_price,
                        CASE 
                            WHEN pv.stock <= 0 THEN 'low'
                            WHEN pv.stock <= 5 THEN 'warning'
                            ELSE 'ok'
                        END as stock_status
                    FROM ProductVariants pv
                    JOIN Products p ON pv.product_id = p.id
                    WHERE p.has_variants = 1
                    ORDER BY p.name, pv.id
                """)
                
                variants_rows = cursor.fetchall()
                variants = []
                
                for row in variants_rows:
                    variant_data = dict(row)
                    
                    # Parse attribute_values
                    try:
                        if variant_data['attribute_values']:
                            if isinstance(variant_data['attribute_values'], str):
                                variant_data['attributes'] = json.loads(variant_data['attribute_values'])
                            else:
                                variant_data['attributes'] = variant_data['attribute_values']
                                
                            # Create a display name for the variant
                            if isinstance(variant_data['attributes'], dict):
                                variant_data['variant_name'] = " / ".join(str(v) for v in variant_data['attributes'].values() if v)
                            else:
                                variant_data['variant_name'] = f"Variant #{variant_data['variant_id']}"
                    except:
                        variant_data['attributes'] = {}
                        variant_data['variant_name'] = f"Variant #{variant_data['variant_id']}"
                        
                    # Calculate stock value
                    variant_price = variant_data.get('variant_price', 0)
                    variant_data['stock_value'] = variant_price * variant_data.get('current_stock', 0)
                        
                    variants.append(variant_data)
                
                # Calculate summary statistics
                total_products = len(products)
                low_stock_products = sum(1 for p in products if p['stock_status'] == 'low')
                warning_stock_products = sum(1 for p in products if p['stock_status'] == 'warning')
                total_stock_value = sum(p.get('stock_value', 0) or 0 for p in products)
                total_retail_value = sum(p.get('retail_value', 0) or 0 for p in products)
                
                # Add variant stock value to total
                total_stock_value += sum(v.get('stock_value', 0) or 0 for v in variants)
                
                summary = {
                    'total_products': total_products,
                    'low_stock_products': low_stock_products,
                    'warning_stock_products': warning_stock_products,
                    'total_stock_value': total_stock_value,
                    'total_retail_value': total_retail_value,
                    'potential_profit': total_retail_value - total_stock_value
                }
                
                return {
                    'summary': summary,
                    'products': products,
                    'variants': variants
                }
            except Exception as e:
                print(f"Error getting inventory report: {e}")
                return None
            finally:
                conn.close()
        return None
