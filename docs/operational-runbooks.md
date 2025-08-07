# Operational Runbooks

## Overview

This document provides operational procedures for maintaining and troubleshooting the Weather Forecast App in production environments.

## Daily Operations

### Morning Health Check (5 minutes)
1. **Check Application Status**
   ```bash
   # Test the application endpoint
   curl -f https://your-cloudfront-domain.cloudfront.net/
   curl -f https://your-api-gateway-url/health
   ```

2. **Review CloudWatch Dashboard**
   - Navigate to the main CloudWatch dashboard
   - Check for any red metrics or anomalies
   - Verify API response times are < 2 seconds
   - Confirm error rates are < 1%

3. **Check Active Alarms**
   ```bash
   aws cloudwatch describe-alarms --state-value ALARM --region eu-west-1
   ```

### Evening Review (10 minutes)
1. **Cost Monitoring**
   - Review cost dashboard for daily spend
   - Check if costs are tracking within budget
   - Identify any cost spikes

2. **Log Review**
   - Check CloudWatch logs for ERROR entries
   - Review any unusual patterns in API usage
   - Verify weather data is being cached properly

## Weekly Operations

### Monday: Performance Review (15 minutes)
1. **Performance Metrics Analysis**
   - Lambda function duration trends
   - API Gateway latency patterns
   - DynamoDB read/write capacity utilization
   - Cache hit/miss ratios

2. **Capacity Planning**
   - Review traffic patterns from the past week
   - Identify peak usage times
   - Plan for any expected traffic increases

### Wednesday: Security Review (10 minutes)
1. **Access Logs Review**
   - Check CloudFront access logs for unusual patterns
   - Review API Gateway access logs for suspicious requests
   - Verify no unauthorized access attempts

2. **IAM Permissions Audit**
   - Ensure no overly permissive policies
   - Check for unused IAM roles or policies

### Friday: Maintenance Tasks (20 minutes)
1. **Dependency Updates**
   - Check for Python package updates in requirements.txt
   - Review Terraform provider updates
   - Plan maintenance windows for updates

2. **Backup Verification**
   - Verify DynamoDB point-in-time recovery is enabled
   - Test backup restoration procedures (quarterly)

## Monthly Operations

### First Monday: Cost Optimization (30 minutes)
1. **Cost Analysis**
   - Review monthly cost breakdown by service
   - Compare costs to previous months
   - Identify optimization opportunities

2. **Resource Right-Sizing**
   - Analyze Lambda memory utilization
   - Review DynamoDB capacity settings
   - Optimize CloudWatch log retention if needed

### Mid-Month: Performance Optimization (45 minutes)
1. **Performance Tuning**
   - Analyze Lambda cold start metrics
   - Review API response time percentiles
   - Optimize caching strategies if needed

2. **Load Testing**
   - Run synthetic load tests
   - Verify auto-scaling behavior
   - Test failure scenarios

### End of Month: Reporting (15 minutes)
1. **Generate Monthly Report**
   - Availability metrics (target: 99.9%)
   - Performance metrics (target: <2s response time)
   - Cost summary and trends
   - Security incidents (target: 0)

## Incident Response Procedures

### High Priority Incidents

#### Application Down (P1)
**Symptoms**: Health check failures, 5xx errors > 50%

**Response Steps**:
1. **Immediate (0-5 minutes)**
   ```bash
   # Check service status
   aws lambda get-function --function-name weather-forecast-app-lambda
   aws apigateway get-rest-apis
   aws dynamodb describe-table --table-name weather-forecast-app-cache
   ```

2. **Investigation (5-15 minutes)**
   - Check CloudWatch logs for Lambda errors
   - Review API Gateway metrics
   - Verify DynamoDB connectivity
   - Check external weather API status

3. **Resolution (15-30 minutes)**
   - If Lambda issue: Redeploy function or increase memory
   - If API Gateway issue: Check configuration and redeploy
   - If DynamoDB issue: Check capacity and permissions
   - If external API issue: Implement fallback or cached responses

#### High Error Rate (P2)
**Symptoms**: Error rate > 5%, but service partially functional

**Response Steps**:
1. **Identify Error Pattern**
   ```bash
   # Query recent errors
   aws logs filter-log-events \
     --log-group-name /aws/lambda/weather-forecast-app-lambda \
     --start-time $(date -d '1 hour ago' +%s)000 \
     --filter-pattern 'ERROR'
   ```

2. **Analyze Root Cause**
   - Check for specific error messages
   - Identify affected cities or endpoints
   - Review recent deployments or changes

3. **Implement Fix**
   - Apply hotfix if code issue
   - Adjust configuration if infrastructure issue
   - Scale resources if capacity issue

### Medium Priority Incidents

#### High Latency (P3)
**Symptoms**: Response times > 5 seconds

**Response Steps**:
1. **Performance Analysis**
   - Check Lambda duration metrics
   - Review API Gateway latency
   - Analyze DynamoDB response times
   - Check external weather API response times

2. **Optimization Actions**
   - Increase Lambda memory if CPU-bound
   - Optimize database queries
   - Implement additional caching
   - Consider provisioned concurrency

#### Cost Alert (P3)
**Symptoms**: Budget threshold exceeded

**Response Steps**:
1. **Cost Investigation**
   ```bash
   # Get cost breakdown
   aws ce get-cost-and-usage \
     --time-period Start=2024-01-01,End=2024-01-31 \
     --granularity MONTHLY \
     --metrics BlendedCost \
     --group-by Type=DIMENSION,Key=SERVICE
   ```

2. **Identify Cost Drivers**
   - Review API Gateway request volume
   - Check Lambda invocation count
   - Analyze DynamoDB read/write operations
   - Review CloudFront data transfer

3. **Cost Optimization**
   - Implement request throttling if needed
   - Optimize caching to reduce API calls
   - Right-size Lambda memory allocation

## Maintenance Procedures

### Planned Maintenance Windows

#### Monthly Dependency Updates
**Schedule**: First Saturday of each month, 2:00 AM UTC

**Procedure**:
1. **Pre-maintenance**
   - Create backup of current configuration
   - Notify stakeholders of maintenance window
   - Prepare rollback plan

2. **Maintenance Steps**
   ```bash
   # Update Python dependencies
   pip install -r requirements.txt --upgrade

   # Update Terraform providers
   terraform init -upgrade

   # Plan and apply changes
   terraform plan
   terraform apply
   ```

3. **Post-maintenance**
   - Verify application functionality
   - Run smoke tests
   - Monitor for 30 minutes post-deployment

#### Quarterly Security Updates
**Schedule**: First Saturday of each quarter, 3:00 AM UTC

**Procedure**:
1. **Security Scan**
   - Run security vulnerability scans
   - Review IAM permissions
   - Check for outdated dependencies

2. **Apply Updates**
   - Update all dependencies with security patches
   - Apply infrastructure security updates
   - Update SSL certificates if needed

3. **Security Validation**
   - Run penetration tests
   - Verify security controls
   - Update security documentation

### Emergency Procedures

#### Rollback Procedure
**When to Use**: Critical issues after deployment

**Steps**:
1. **Immediate Rollback**
   ```bash
   # Rollback to previous Terraform state
   terraform apply -target=module.backend -var-file=previous.tfvars

   # Or rollback Lambda function
   aws lambda update-function-code \
     --function-name weather-forecast-app-lambda \
     --zip-file fileb://previous-version.zip
   ```

2. **Verify Rollback**
   - Test application functionality
   - Check error rates return to normal
   - Verify performance metrics

#### Disaster Recovery
**Scenario**: Complete region failure

**Recovery Steps**:
1. **Assess Damage**
   - Determine scope of outage
   - Check data integrity
   - Estimate recovery time

2. **Activate DR Plan**
   ```bash
   # Deploy to backup region
   terraform workspace select dr
   terraform apply -var-file=dr.tfvars

   # Update DNS to point to DR region
   aws route53 change-resource-record-sets \
     --hosted-zone-id Z123456789 \
     --change-batch file://dr-dns-change.json
   ```

3. **Data Recovery**
   - Restore DynamoDB from point-in-time backup
   - Verify data consistency
   - Resume normal operations

## Monitoring and Alerting

### Key Metrics to Monitor

#### Application Health
- **API Gateway 5xx Error Rate**: < 1%
- **Lambda Error Rate**: < 1%
- **Lambda Duration**: < 25 seconds (timeout is 30s)
- **DynamoDB Throttling**: 0 events

#### Performance Metrics
- **API Response Time**: < 2 seconds (95th percentile)
- **Lambda Cold Start Rate**: < 10%
- **Cache Hit Rate**: > 80%
- **Weather API Success Rate**: > 95%

#### Business Metrics
- **Daily Active Users**: Track via CloudFront logs
- **API Requests per Day**: Monitor usage patterns
- **Geographic Distribution**: Analyze user locations

### Alert Escalation

#### Level 1: Automated Response
- Restart Lambda function if memory issues
- Scale DynamoDB capacity if throttling
- Clear CloudFront cache if stale content

#### Level 2: On-Call Engineer
- High error rates requiring investigation
- Performance degradation
- Security incidents

#### Level 3: Management Escalation
- Extended outages (> 1 hour)
- Data breaches or security incidents
- Budget overruns > 50%

## Contact Information

### On-Call Rotation
- **Primary**: Platform Team Lead
- **Secondary**: Senior DevOps Engineer
- **Escalation**: Engineering Manager

### External Contacts
- **AWS Support**: Enterprise support case
- **Weather API Support**: api.met.no support
- **DNS Provider**: Route 53 or external DNS provider

## Documentation Updates

This runbook should be reviewed and updated:
- **Monthly**: Update procedures based on lessons learned
- **Quarterly**: Review contact information and escalation procedures
- **After Incidents**: Update procedures based on incident findings
- **After Changes**: Update procedures when infrastructure changes

---

**Last Updated**: January 2024  
**Next Review**: February 2024  
**Owner**: Platform Team