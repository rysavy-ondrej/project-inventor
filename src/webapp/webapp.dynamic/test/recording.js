const puppeteer = require('puppeteer'); // v23.0.0 or later

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    const timeout = 5000;
    page.setDefaultTimeout(timeout);

    {
        const targetPage = page;
        await targetPage.setViewport({
            width: 1629,
            height: 471
        })
    }
    {
        const targetPage = page;
        await targetPage.goto('https://csu.gov.cz/');
    }
    {
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
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(Otevřít submenu Společnost[role=\\"link\\"])'),
            targetPage.locator('#csu-header-button-subnav-0-1'),
            targetPage.locator('::-p-xpath(//*[@id=\\"csu-header-button-subnav-0-1\\"])'),
            targetPage.locator(':scope >>> #csu-header-button-subnav-0-1')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 82.14285278320312,
                y: 32.99998474121094,
              },
            });
    }
    {
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
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(Otevřít submenu Metodika[role=\\"link\\"])'),
            targetPage.locator('#csu-header-button-main-nav-subnav-2'),
            targetPage.locator('::-p-xpath(//*[@id=\\"csu-header-button-main-nav-subnav-2\\"])'),
            targetPage.locator(':scope >>> #csu-header-button-main-nav-subnav-2')
        ])
            .setTimeout(timeout)
            .click({
              offset: {
                x: 26.84814453125,
                y: 49,
              },
            });
    }
    {
        const targetPage = page;
        const promises = [];
        const startWaitingForEvents = () => {
            promises.push(targetPage.waitForNavigation());
        }
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(Číselníky[role=\\"link\\"])'),
            targetPage.locator('li.is-open li:nth-of-type(2) > a'),
            targetPage.locator('::-p-xpath(//*[@id=\\"csu-header-main-nav-subnav-2\\"]/div/div/div[1]/ul/li[2]/a)'),
            targetPage.locator(':scope >>> li.is-open li:nth-of-type(2) > a'),
            targetPage.locator('::-p-text(Číselníky)')
        ])
            .setTimeout(timeout)
            .on('action', () => startWaitingForEvents())
            .click({
              offset: {
                x: 84.14285278320312,
                y: 33.99998474121094,
              },
            });
        await Promise.all(promises);
    }

    await browser.close();

})().catch(err => {
    console.error(err);
    process.exit(1);
});
