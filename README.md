# CST8919-A1

## Set up the project

1. Fork this repository, make sure the repository is public accessible.

2. Set up an application on Auth0, and grant the following credentials:
```
AUTH0_CLIENT_ID
AUTH0_CLIENT_SECRET
AUTH0_DOMAIN
APP_SECRET_KEY
``` 

3. Configure callback urls, etc. on Auth0. (Please refer to [Lab1](https://github.com/Zhiyuanlu000217/cst8919-lab1))

4. Go to Azure portal > App Services > Create > Web App, and fill in the following information(The rest are optional)
- Publish: Code
- Runtime Stack: Python 3.10

Then go to Deployment tab, enable `Continuous deployment` and choose the repository, keep everything else by default, review and create the service.

5. Once the service is created, first go to Settings > Environment variables, fill in the Auth0 credentials manually, and click `apply`.

6. Then, go to Overview, copy the default domain, which looks like `cst8919-a1-aqb3e5dhd6fvdmb2.canadacentral-01.azurewebsites.net`, and add this to Auth0 callback links, allowed domain, etc.

7. Once appy the change on Auth0, wait for 30 seconds, and goto Overview > Browse, try to login the app, now it should work.

8. Go to Monitoring > Log Stream, and interact with the website, you should be able to see some new log generated.

9. Go to Monitoring >  Diagnostic Settings > Add diagnostic setting > Choose `App Service Console Logs ` and `Send to Log Analytics workspace`

10. Go to Monitoring > Alerts > Create Alert rules, choose the following:
- Signal name: Custom log search
- Query type: Aggregated logs
- Search query:
```
AppServiceConsoleLogs
| where ResultDescription has "Protected route accessed by user"
| where TimeGenerated > ago(15m)
| extend user_id = extract(@"user_id: ([^,]+)", 1, ResultDescription)
| summarize access_count = count(), last_access = max(TimeGenerated) by user_id
| where access_count > 10
| project user_id, last_access, access_count
```
- Measurement
    - Measure: access_count
    - Aggregation type: Total
    - Aggregation granularity: 15 mins

- Split by dimensions: Dimension name: user_id
- Alert logic
    - Operator: Greater than
    - Threshold value: 10
    - Frequency of evaluation: 15 mins

Then go to Actions tab, choose "Use quick actions (preview)", fill out information, and create the alert.

11. Trigger the '/protected' route 10 times, you should receive email of alert within couple minutes.

## Explanation of logging, detection logic

### Logging

| Route | Event/Condition | Log Level | Log Message |
|-------|-----------------|-----------|-------------|
| `/` | Home page accessed | INFO | Home page accessed |
| `/login` | Login page accessed | INFO | Login page accessed |
| `/callback` | Successful login | INFO | Successful login for `user: {email} - user_id: {user_id}, timestamp: {timestamp}` |
| `/callback` | Failed login | WARNING | Failed login attempt: `{error_message}` |
| `/logout` | User logs out | INFO | User logout: `{email} - user_id: {user_id}, timestamp: {timestamp}` |
| `/protected` | Unauthorized access | WARNING | Unauthorized access attempt to /protected - `timestamp: {timestamp}` |
| `/protected` | Authorized access | INFO | Protected route accessed by user: `{email} - user_id: {user_id}, timestamp: {timestamp}` |

### KQL Query
```
AppServiceConsoleLogs
| where ResultDescription has "Protected route accessed by user"
| where TimeGenerated > ago(15m)
| extend user_id = extract(@"user_id: ([^,]+)", 1, ResultDescription)
| summarize access_count = count(), last_access = max(TimeGenerated) by user_id
| where access_count > 10
| project user_id, last_access, access_count
```

Explaination:
- Selects the log table
- Filters for logs with level "Error"
- Further filters for logs mentioning "Failed login attempt"
- Only includes logs from the last 30 minutes
- Shows only the timestamp, log level, and full log message in the results


### Alert
- Runs the query every 15 minutes.
- Counts how many times each user accesses /protected in the last 15 minutes.
- Triggers an alert if any user exceeds 10 accesses in that window.
- Evaluates each user (user_id) separately.
- Notifies you via the configured action group.

