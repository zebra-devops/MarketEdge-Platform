Database Schema Overview
The application uses several main entities to manage pricing tests, insights, and analysis. Each entity is like a table in a database, and the "properties" are the columns in that table.

Built-in Attributes (for all entities): Every record in every entity automatically includes these fields:

id (Unique identifier for the record)
created_date (Timestamp when the record was created)
updated_date (Timestamp when the record was last updated)
created_by (Email of the user who created the record)
Entities & Key Attributes:
User

id: Unique user ID.
email: User's email address (unique, used as created_by).
full_name: User's full name.
role: User's role (e.g., 'admin', 'user').
feature_flags: JSON object for user-specific feature toggles (e.g., {"geolift_analysis_enabled": true}).
Hypothesis (Represents an insight or a testable idea)

id: Unique hypothesis ID.
title: Brief statement of the insight/hypothesis.
description: More detailed explanation.
status: (e.g., 'proposed', 'in_testing', 'validated', 'disproven', 'archived').
expected_revenue_impact: Estimated financial value.
confidence_level: (e.g., 'low', 'medium', 'high').
source_observation: The data or event that led to this hypothesis.
tags: Array of keywords for categorization.
last_validated_date: Date when the hypothesis was last proven true by a test.
evidence_count: Number of tests that validated this hypothesis.
is_demo_data: Boolean, indicates if it's sample data.
Experiment (Represents a pricing test)

id: Unique experiment ID.
name: Name of the pricing test.
description: Detailed description of the test.
status: (e.g., 'draft', 'planned', 'running', 'completed', 'banked', 'archived').
test_type: (e.g., 'geolift', 'price_elasticity', 'promotional_pricing').
primary_kpi: The main metric being optimized.
pricing_change: Description of the pricing intervention (e.g., 'Base price increased by 10%').
start_date: Start date of the test.
end_date: End date of the test.
markets: Array of geographical markets involved.
expected_revenue_impact: Anticipated financial impact.
hypothesis: The specific hypothesis being tested.
source_insight_id: Foreign Key to Hypothesis.id (if based on an existing insight).
source_insight_title: Title of the source insight (for display convenience).
insight_source_type: (e.g., 'validated_insight', 'observation').
results: JSON object containing test outcomes (e.g., revenue_lift_percentage, revenue_impact_gbp, confidence_level).
consultant_commentary: Detailed notes from a consultant after review.
is_demo_data: Boolean, indicates if it's sample data.
Chart (Represents a visual artifact from an experiment)

id: Unique chart ID.
experiment_id: Foreign Key to Experiment.id (the test this chart belongs to).
file_url: URL of the uploaded chart image.
caption: Description or title for the chart.
category: Type of chart (e.g., 'time_series', 'demand_response').
is_key_chart: Boolean, marks it as a primary visual.
AnalysisRun (Records an instance of a statistical analysis tool being run)

id: Unique analysis run ID.
name: Name given to this analysis run.
analysis_type: (e.g., 'geolift').
status: (e.g., 'in_progress', 'awaiting_review', 'validated', 'implemented').
result_summary: Short summary of the analysis outcome.
linked_experiment_id: Foreign Key to Experiment.id (if this analysis is for a specific test).
is_demo_data: Boolean, indicates if it's sample data.
Relationships (How Data Connects):
+----------------+       +-------------------+       +---------------+
|     User       |<------|     Hypothesis    |       |    Chart      |
|----------------| created_by |-------------------|       |---------------|
| id             |       | id                |       | id            |
| email          |       | title             |       | experiment_id*|
| full_name      |       | description       |       | file_url      |
| role           |       | status            |       | caption       |
| feature_flags  |       | expected_revenue  |       | category      |
+----------------+       | confidence_level  |       | is_key_chart  |
          ^              | source_observation|       +---------------+
          |              | ...               |               ^
          |              +-------------------+               |
          |                        ^                         |
          |                        | many-to-one             | one-to-many
          |                        | (Experiment.source_insight_id)
          |                        |                         |
          |              +-------------------+               |
          |              |    Experiment     |               |
          |------------->|-------------------|---------------+
created_by             | id                |               |
                       | name              |               |
                       | description       |               |
                       | status            |               |
                       | test_type         |               |
                       | pricing_change    |               |
                       | start_date        |               |
                       | end_date          |               |
                       | markets           |               |
                       | expected_revenue  |               |
                       | hypothesis        |               |
                       | source_insight_id*|               |
                       | source_insight_title|             |
                       | results (JSON)    |               |
                       | ...               |               |
                       +-------------------+               |
                                 ^                         |
                                 | one-to-many             |
                                 | (AnalysisRun.linked_experiment_id)
                                 |                         |
                                 +-------------------------+
                                 |      AnalysisRun        |
                                 |-------------------------|
                                 | id                      |
                                 | name                    |
                                 | analysis_type           |
                                 | status                  |
                                 | result_summary          |
                                 | linked_experiment_id*   |
                                 | ...                     |
                                 +-------------------------+
Explanation of Relationships:

User (created_by) <---> All Entities: Every entity tracks the User who created it via the created_by field, linking back to User.email.
Experiment <---> Hypothesis: An Experiment can be linked to a Hypothesis as its source_insight_id. This means multiple experiments can test the same fundamental hypothesis (many-to-one from Experiment to Hypothesis).
Experiment <---> Chart: An Experiment can generate many Charts, so Charts have an experiment_id pointing to the Experiment they belong to (one-to-many from Experiment to Chart).
Experiment <---> AnalysisRun: An AnalysisRun (e.g., a Geolift analysis) is often performed for a specific Experiment, so it includes a linked_experiment_id (one-to-many from Experiment to AnalysisRun).
This structure allows you to build a comprehensive system for managing your pricing tests, from initial insights to detailed results and analyses.