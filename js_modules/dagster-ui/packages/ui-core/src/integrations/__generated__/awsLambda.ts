/**
 * THIS FILE IS GENERATED BY `yarn generate-integration-docs`.
 *
 * DO NOT EDIT MANUALLY.
 */

import {IntegrationFrontmatter} from '../types';
import awsLambdaLogo from './logos/aws-lambda.svg';

export const logo = awsLambdaLogo;

export const frontmatter: IntegrationFrontmatter = {
  id: 'awsLambda',
  status: 'published',
  name: 'Lambda',
  title: 'Dagster & AWS Lambda',
  excerpt:
    'Using the AWS Lambda integration with Dagster, you can leverage serverless functions to execute external code in your pipelines.',
  partnerlink: 'https://aws.amazon.com/',
  categories: ['Compute'],
  enabledBy: [],
  enables: [],
  tags: ['dagster-supported', 'compute'],
};

export const content =
  'Using this integration, you can leverage AWS Lambda to execute external code as part of your Dagster pipelines. This is particularly useful for running serverless functions that can scale automatically and handle various workloads without the need for managing infrastructure. The `PipesLambdaClient` class allows you to invoke AWS Lambda functions and stream logs and structured metadata back to Dagster\'s UI and tools.\n\n### Installation\n\n```bash\npip install dagster-aws\n```\n\n### Examples\n\n<CodeExample path="docs_snippets/docs_snippets/integrations/aws-lambda.py" language="python" />\n\n### About AWS Lambda\n\n**AWS Lambda** is a serverless compute service provided by Amazon Web Services (AWS). It allows you to run code without provisioning or managing servers. AWS Lambda automatically scales your application by running code in response to each trigger, such as changes to data in an Amazon S3 bucket or an update to a DynamoDB table. You can use AWS Lambda to extend other AWS services with custom logic, or create your own backend services that operate at AWS scale, performance, and security.';
