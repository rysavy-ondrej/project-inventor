# How detection of page changed works in user session recording

## How it works
The detection of page changes relies on monitoring the presence or absence of specific DOM elements. If a targeted element cannot be found, it is indicating that page has changed

## Key Steps
### 1. Targeting an Element:
A selector (e.g., CSS or XPath) is provided for a specific element expected to be present on the page
### 2. Checking Element Presence:
Puppeteer recording uses method targetPage.locator() to locate the element.
```javascript
       const targetPage = page;
        const promises = [];
        const startWaitingForEvents = () => {
            promises.push(targetPage.waitForNavigation());
        }
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(Kultura, média, sport[role=\\"menuitem\\"]) >>>> ::-p-aria([role=\\"link\\"])'),
            targetPage.locator('#csu-header-subnav-0-1 > li:nth-of-type(3) > a'),
            targetPage.locator('::-p-xpath(//*[@id=\\"csu-header-subnav-0-1\\"]/li[3]/a)'),
            targetPage.locator(':scope >>> #csu-header-subnav-0-1 > li:nth-of-type(3) > a')
        ])
            .setTimeout(timeout)
            .on('action', () => startWaitingForEvents())
            .click({
              offset: {
                x: 78.142822265625,
                y: 29,
              },
            });
        await Promise.all(promises);
```
### 3. Handling Missing Elements:
If the element is not found within the specified element_search_timeout period, the library assumes the page has changed.
## Limitations
While this method is simple and effective in many scenarios, it has several limitations:
### 1. Event Handling Limitations:
Puppeteer recordings do not include certain user interactions like mouseover and mouseenter which may lead to elements not being visible or accessible when the script is executed.
In this scenario, this would result in a page_changed status, although the page has not been changed. 

Possible workaround:
* It is possible to edit the recording in google chrome and add hover step that will take care of for example opening the dropdown menu
* Use a combination of click and focus events for
dropdowns and modals instead of relying on hover.
### 2. Replay Interacts with an Irrelevant Element
If the recorded selector matches an unintended element due to changes on the page (e.g., the login input is replaced with a search bar)<br>
In this scenario, the analysis will result in a completed status even if the page has been changed.
