-- Enable RLS on all tenant-specific tables
-- Only applies to tables that actually have a tenant_id column
-- Uses CONTINUE WHEN to skip tables missing the column

DO $$
DECLARE
    t TEXT;
    has_col BOOLEAN;
    all_tables TEXT[] := ARRAY[
        'scope','scopedependency','risk','riskquantificationprofile','riskscope',
        'control','incident','exception','assessment','evidence',
        'assessmentresponse','finding','correctiveaction',
        'processingactivity','datasubjectrequest','processoragreement',
        'continuityplan','continuitytest','document','riskappetite',
        'managementreview','complianceplanningitem','initiative',
        'reviewschedule','auditlog','notification','comment',
        'attachment','maturityassessment','policy','organizationcontext',
        'organizationprofile','knowledgeartifact','dashboard',
        'aitoolexecution','aiconversation','aisuggestion','objective',
        'tag','entitytag','tenantsetting','integrationconfig',
        'reporttemplate','scheduledreport','reportexecution',
        'workflowinstance','backlogitem','userscoperole',
        'standard','requirement',
        'assessmentquestion','biathreshold','aiknowledgebase',
        'aiprompttemplate','aiagent','workflowdefinition'
    ];
    -- Tables where tenant_id can be NULL (shared/global data)
    shared_tables TEXT[] := ARRAY[
        'assessmentquestion','biathreshold','aiknowledgebase',
        'aiprompttemplate','aiagent','workflowdefinition'
    ];
    is_shared BOOLEAN;
BEGIN
    FOREACH t IN ARRAY all_tables LOOP
        -- Check if table exists and has tenant_id column
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = t
              AND column_name = 'tenant_id'
        ) INTO has_col;

        IF NOT has_col THEN
            RAISE NOTICE 'Skipping % (no tenant_id column)', t;
            CONTINUE;
        END IF;

        -- Enable RLS
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I', t);

        -- Check if shared table
        is_shared := t = ANY(shared_tables);

        IF is_shared THEN
            EXECUTE format(
                'CREATE POLICY tenant_isolation ON %I USING (tenant_id = current_setting(''app.current_tenant'')::integer OR tenant_id IS NULL)',
                t
            );
            RAISE NOTICE 'RLS (shared) enabled on %', t;
        ELSE
            EXECUTE format(
                'CREATE POLICY tenant_isolation ON %I USING (tenant_id = current_setting(''app.current_tenant'')::integer)',
                t
            );
            RAISE NOTICE 'RLS (strict) enabled on %', t;
        END IF;
    END LOOP;
END $$;
