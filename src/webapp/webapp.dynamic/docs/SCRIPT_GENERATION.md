# How generation of script works

## How it works
'replay_script' is user session recording from Chrome encoded in Base64. 
## Key Steps
### 1. Decoding of replay_script:
User session recording from Chrome is decoded
### 2. First extraction 
Extracts the contents of the outermost pair of curly braces {} from the given script.
### 3. Second extraction 
* Extracts all content between sets of curly braces {} from result of 2. step.
* Returns an array of substrings
* First item contains code that sets the browser window's viewport 
```javascript
const targetPage = page;
await targetPage.setViewport({
    width: 1629,
    height: 471
})
```
* Each other item contains a separate user interaction or visited page
```javascript
// 2. item 
// initial page where user session recording began
const targetPage = page;
await targetPage.goto('https://csu.gov.cz/');
```
```javascript
// 3. item
// click event on element 
const targetPage = page;
await puppeteer.Locator.race([
    targetPage.locator('::-p-aria(Otevřít submenu Statistiky[role=\\"link\\"])'),
    targetPage.locator('#csu-header-button-main-nav-subnav-0'),
    targetPage.locator('::-p-xpath(//*[@id=\\"csu-header-button-main-nav-subnav-0\\"])'),
    targetPage.locator(':scope >>> #csu-header-button-main-nav-subnav-0')
])
    .setTimeout(timeout)
    .click({
        offset: {
            x: 35.73211669921875,
            y: 51,
        },
    });
```
### 3. Inserting additional code 
From the second item, the code for extracting data and taking a screenshot is inserted
### 4. Creating file for eval execution
```javascript
(async () => {{

        const targetPage = page;
        await targetPage.setViewport({
            width: 1629,
            height: 471
        })
    }
{

        const targetPage = page;
        await targetPage.goto('https://csu.gov.cz/');

    await new Promise(resolve => setTimeout(resolve, 200));
    image = await page.screenshot({ encoding: 'base64', fullPage: true  });
    await add_metrics_to_visited_page_item(page);
    visited_page_item.status = "completed"
    total_data_size = 0;
    download_data.visited_pages.push(visited_page_item);
    await init_visited_page_item();

}{

        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(OtevÅÃ­t submenu Statistiky[role=\\"link\\"])'),
            targetPage.locator('#csu-header-button-main-nav-subnav-0'),
            targetPage.locator('::-p-xpath(//*[@id=\\"csu-header-button-main-nav-subnav-0\\"])'),
            targetPage.locator(':scope >>> #csu-header-button-main-nav-subnav-0')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 35.73211669921875,
                y: 51,
              },
            });

    await new Promise(resolve => setTimeout(resolve, 200));
    image = await page.screenshot({ encoding: 'base64', fullPage: true  });
    await add_metrics_to_visited_page_item(page);
    visited_page_item.status = "completed"
    total_data_size = 0;
    download_data.visited_pages.push(visited_page_item);
    await init_visited_page_item();

}
})()
```
