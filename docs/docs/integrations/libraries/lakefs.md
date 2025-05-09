---
title: Dagster & LakeFS
sidebar_label: LakeFS
description: lakeFS provides version control and complete lineage over the data lake.
tags: [community-supported, storage]
source:
pypi: https://pypi.org/project/lakefs-client
sidebar_custom_props:
  logo: images/integrations/lakefs.svg
  community: true
partnerlink: https://lakefs.io/
---

By integrating with lakeFS, a big data scale version control system, you can leverage the versioning capabilities of lakeFS to track changes to your data. This integration allows you to have a complete lineage of your data, from the initial raw data to the transformed and processed data, making it easier to understand and reproduce data transformations.

With lakeFS and Dagster integration, you can ensure that data flowing through your Dagster jobs is easily reproducible. lakeFS provides a consistent view of your data across different versions, allowing you to troubleshoot pipeline runs and ensure consistent results.

Furthermore, with lakeFS branching capabilities, Dagster jobs can run on separate branches without additional storage costs, creating isolation and allowing promotion of only high-quality data to production leveraging a CI/CD pipeline for your data.

### Installation

```bash
pip install lakefs-client
```

### Example

<CodeExample path="docs_snippets/docs_snippets/integrations/lakefs.py" language="python" />

### About lakeFS

**lakeFS** is on a mission to simplify the lives of data engineers, data scientists and analysts providing a data version control platform at scale.
