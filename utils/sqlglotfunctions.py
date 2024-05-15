from sqlglot import optimizer, expressions,transpile,parse_one

################################################################################
################################################################################

# stole this from the internet.
# this qualifies tables columns to their full names
def qualify_columns(expression):
    try:      
        expression = optimizer.qualify_tables.qualify_tables(expression)
        expression = optimizer.isolate_table_selects.isolate_table_selects(expression)
        expression = optimizer.qualify_columns.qualify_columns(expression)

    except:
        pass  
 
    return expression
################################################################################
################################################################################
  
# stole this from the internet.
# this returns a list of dictionaries of all tables and columns in those tables used in the provided sql. 
# dialect is set to tsql - could look at parameterising this. 
def parse_sql(sql_query, dialect='tsql'):

    ast = parse_one(sql_query, read=dialect)
    ast = qualify_columns(ast)
    
    physical_columns = {}
    
    for scope in optimizer.scope.traverse_scope(ast):
        for c in scope.columns:
            if isinstance(scope.sources.get(c.table), expressions.Table):
                table_info = scope.sources.get(c.table)
                full_table_name=table_info.catalog +'.'+table_info.db+'.'+table_info.name
                col_name = {c.name}
                try:
                    physical_columns[full_table_name].add(c.name)
                        
                except KeyError:
                    update = {full_table_name: col_name}
                    physical_columns.update(update)
                
    # convert output into expected input for next step
    return [{'table_name':k, 'columns': list(v)} for k,v in physical_columns.items()]


################################################################################
################################################################################
# this is called to do the T-SQL to DB-SQL translation. 
def sqlglot_transpilation(sql_query):
   return transpile(sql_query, read="tsql", write="spark", pretty=True)[0]