"""
Utility functions for Drug Intelligence Automation
Contains the core logic from Robot Framework resource files
"""
import re
from typing import List, Dict, Any, Tuple
from logger import get_logger


class DrugNameProcessor:
    """Process and transform drug names"""
    
    def __init__(self, excluded_salts: List[str]):
        self.excluded_salts = excluded_salts
        self.logger = get_logger()
    
    def get_excluded_salt_2(self, product_name: str) -> str:
        """
        Remove excluded salts from product name
        This is GET_EXCLUDED_SALT_2 from Robot Framework
        """
        if not product_name:
            return ""
        
        filtered_name = str(product_name).strip()
        
        # Remove each excluded salt (case-insensitive)
        for salt in self.excluded_salts:
            if not salt:
                continue
            # Use word boundaries to avoid partial matches
            pattern = re.compile(r'\b' + re.escape(salt) + r'\b', re.IGNORECASE)
            filtered_name = pattern.sub('', filtered_name)
        
        # Clean up extra spaces
        filtered_name = ' '.join(filtered_name.split())
        
        return filtered_name.strip()
    
    def process_drug_names(self, db, table_name: str, process_id: str):
        """
        Process drug names - extract and standardize
        This is PROCESS_DRUG_NAMES from Robot Framework
        """
        try:
            self.logger.info(f"Processing drug names from table: {table_name}")
            
            # Get all records for this process
            query = f"""
                SELECT * FROM {table_name} 
                WHERE process_id = '{process_id}'
            """
            records = db.execute_query(query)
            
            processed_count = 0
            for record in records:
                # Extract active ingredients or product name
                drug_name = record.get('active_ingrediants') or record.get('productname', '')
                
                if drug_name:
                    # Process the drug name (already filtered in processors)
                    # Additional processing can be added here
                    processed_count += 1
            
            self.logger.info(f"Processed {processed_count} drug names from {table_name}")
            
        except Exception as e:
            self.logger.error(f"Error processing drug names: {str(e)}", exc_info=True)
            raise


class MasterTrackerProcessor:
    """Process Master Tracker data"""
    
    def __init__(self):
        self.logger = get_logger()
    
    def transform_to_dict(self, mt_values: List[List], customer_names: List[str]) -> List[Dict]:
        """
        Transform Master Tracker values to dictionary format
        This is Transform To Dict from Robot Framework
        """
        try:
            result = []
            
            for row in mt_values:
                if not row or len(row) < len(customer_names) + 1:
                    continue
                
                row_dict = {}
                
                # First column is product name
                product_name = row[0] if row else ''
                row_dict['productname'] = {
                    'original': product_name,
                    'processed': [product_name]  # Will be enriched with synonyms
                }
                
                # Remaining columns are customer data
                for idx, customer_name in enumerate(customer_names):
                    customer_value = row[idx + 1] if len(row) > idx + 1 else ''
                    row_dict[customer_name] = customer_value
                
                result.append(row_dict)
            
            self.logger.info(f"Transformed {len(result)} Master Tracker rows to dict")
            return result
            
        except Exception as e:
            self.logger.error(f"Error transforming to dict: {str(e)}", exc_info=True)
            raise
    
    def find_synonyms(self, drug_names: List[str], synonyms_values: List[List]) -> List[str]:
        """
        Find and add drug name synonyms
        This is Find Synonyms from Robot Framework
        """
        try:
            collective_names = set(drug_names)
            
            # synonyms_values format: [[drug_name, synonym1, synonym2, ...], ...]
            for synonym_row in synonyms_values:
                if not synonym_row or len(synonym_row) < 2:
                    continue
                
                main_drug = synonym_row[0]
                synonyms = [s for s in synonym_row[1:] if s]
                
                # If any drug name matches, add all synonyms
                for drug in drug_names:
                    if drug.lower() == main_drug.lower():
                        collective_names.update(synonyms)
                        break
            
            self.logger.info(f"Found {len(collective_names)} total drug names including synonyms")
            return list(collective_names)
            
        except Exception as e:
            self.logger.error(f"Error finding synonyms: {str(e)}", exc_info=True)
            return drug_names


class ReportGenerator:
    """Generate reports from processed data"""
    
    def __init__(self, db, config, excel_handler):
        self.db = db
        self.config = config
        self.excel_handler = excel_handler
        self.logger = get_logger()
    
    def generate_overall_count_report(self, process_id: str):
        """Generate overall count report"""
        try:
            self.logger.info("Generating overall count report")
            
            # Get customer reports
            customers = [
                ('Caplin', self.config.get_table_name('caplin_master_report')),
                ('Bells', self.config.get_table_name('bells_master_report')),
                ('Relonchem', self.config.get_table_name('relonchem_master_report')),
                ('Marksans USA', self.config.get_table_name('marksans_usa_master_report')),
                ('Padagis Israel', self.config.get_table_name('padagis_israle_master_report')),
                ('Padagis USA', self.config.get_table_name('padagis_usa_master_report'))
            ]
            
            overall_table = self.config.get_table_name('overall_count_report')
            
            for customer_name, table_name in customers:
                # Count total, included, excluded
                query = f"""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN include_exclude_status = 'include' THEN 1 ELSE 0 END) as included,
                        SUM(CASE WHEN include_exclude_status = 'exclude' THEN 1 ELSE 0 END) as excluded
                    FROM {table_name}
                    WHERE process_id = '{process_id}'
                """
                result = self.db.execute_query(query)
                
                if result:
                    counts = result[0]
                    # Insert into overall report
                    insert_query = f"""
                        INSERT INTO {overall_table}
                        (process_id, customer_name, total_count, included_count, excluded_count, created_datetime)
                        VALUES ('{process_id}', '{customer_name}', {counts['total']}, 
                                {counts['included']}, {counts['excluded']}, NOW())
                    """
                    self.db.execute_insert(insert_query)
            
            self.logger.info("Overall count report generated")
            
        except Exception as e:
            self.logger.error(f"Error generating overall count report: {str(e)}", exc_info=True)
            raise
    
    def generate_inclusion_exclusion_report(self, process_id: str):
        """Generate inclusion/exclusion count report"""
        try:
            self.logger.info("Generating inclusion/exclusion report")
            
            customers = [
                ('Caplin', self.config.get_table_name('caplin_master_report')),
                ('Bells', self.config.get_table_name('bells_master_report')),
                ('Relonchem', self.config.get_table_name('relonchem_master_report')),
                ('Marksans USA', self.config.get_table_name('marksans_usa_master_report')),
                ('Padagis Israel', self.config.get_table_name('padagis_israle_master_report')),
                ('Padagis USA', self.config.get_table_name('padagis_usa_master_report'))
            ]
            
            ie_table = self.config.get_table_name('inclusion_exclusion_counts')
            
            for customer_name, table_name in customers:
                # Group by remark and count
                query = f"""
                    SELECT 
                        remark,
                        include_exclude_status,
                        COUNT(*) as count
                    FROM {table_name}
                    WHERE process_id = '{process_id}'
                    GROUP BY remark, include_exclude_status
                """
                results = self.db.execute_query(query)
                
                for row in results:
                    insert_query = f"""
                        INSERT INTO {ie_table}
                        (process_id, customer_name, remark, status, count, created_datetime)
                        VALUES ('{process_id}', '{customer_name}', '{row['remark']}',
                                '{row['include_exclude_status']}', {row['count']}, NOW())
                    """
                    self.db.execute_insert(insert_query)
            
            self.logger.info("Inclusion/exclusion report generated")
            
        except Exception as e:
            self.logger.error(f"Error generating inclusion/exclusion report: {str(e)}", exc_info=True)
            raise
    
    def create_excel_report(self, process_id: str, output_path: str):
        """Create Excel report with all data"""
        try:
            self.logger.info(f"Creating Excel report: {output_path}")
            
            sheets_data = {}
            
            # Get overall counts
            overall_query = f"""
                SELECT customer_name, total_count, included_count, excluded_count
                FROM {self.config.get_table_name('overall_count_report')}
                WHERE process_id = '{process_id}'
            """
            overall_data = self.db.execute_query(query)
            
            # Format for Excel
            overall_sheet = [['Customer', 'Total', 'Included', 'Excluded']]
            for row in overall_data:
                overall_sheet.append([
                    row['customer_name'],
                    row['total_count'],
                    row['included_count'],
                    row['excluded_count']
                ])
            
            sheets_data['Overall Counts'] = overall_sheet
            
            # Get inclusion/exclusion counts
            ie_query = f"""
                SELECT customer_name, remark, status, count
                FROM {self.config.get_table_name('inclusion_exclusion_counts')}
                WHERE process_id = '{process_id}'
                ORDER BY customer_name, remark
            """
            ie_data = self.db.execute_query(ie_query)
            
            ie_sheet = [['Customer', 'Remark', 'Status', 'Count']]
            for row in ie_data:
                ie_sheet.append([
                    row['customer_name'],
                    row['remark'],
                    row['status'],
                    row['count']
                ])
            
            sheets_data['Inclusion Exclusion'] = ie_sheet
            
            # Create Excel file
            self.excel_handler.create_report_excel(output_path, sheets_data)
            
            self.logger.info(f"Excel report created: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating Excel report: {str(e)}", exc_info=True)
            raise
