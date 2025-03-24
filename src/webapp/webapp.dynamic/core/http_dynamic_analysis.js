const puppeteer = require('puppeteer');
const fs = require('fs');
const  generate_script = require('./script_generator');
const {TimeoutError} = require("puppeteer");

global.download_data = {
    'status': "",
    'visited_pages': [],
};

global.visited_page_item = {
    'current_url': "",
    'status': "",
    'load_time': '',
    'dom_content_loaded_time': '',
    'total_data_size': 0,
    'waterfall_analysis': [],
    'image': "",

};

global.total_data_size = 0;
global.image = 0;


// used in script_generator.js
function init_visited_page_item(){
    visited_page_item = {
        'current_url': "",
        'status': "",
        'load_time': '',
        'dom_content_loaded_time': '',
        'total_data_size': 0,
        'waterfall_analysis': [],
        'image': "",

    };
}

 function write_output_to_console(data) {
     console.log(JSON.stringify(data, null, 4))
 }

function validateParams(params) {

      if ("timeout" in params) {
        if (!Number.isInteger(params.timeout)) {
            download_data =  {status:"error",error_msg: "timeout must be an integer in milliseconds"};
            write_output_to_console(download_data)
            process.exit(0);
        }
    } else {
        params.timeout = 30000;
    }
    if ("element_search_timeout" in params) {
        if (!Number.isInteger(params.element_search_timeout)) {
            download_data =  {status:"error",error_msg: "element search timeout must be an integer in milliseconds"};
            write_output_to_console(download_data)
            process.exit(0);
        }
    } else {
        params.element_search_timeout = 5000;
    }

    if ("timing_between_steps" in params) {
        if (typeof params.timing_between_steps !== "number") {
            download_data =  {status:"error",error_msg: "timing_between_steps timing must be numeric"};
            write_output_to_console(download_data)
            process.exit(0);
        }
    } else {
        params.timing_between_steps = 200;
    }


    if(("replay_script" in params && params.replay_script))
        return params;

    if (!("target_host" in params && params.target_host  )) {
        download_data =  {status:"error",error_msg: "target_host  or replay_script parameter must be provided"};
        write_output_to_console(download_data)
        process.exit(0);
    }
    if ("screenshot_timing_type" in params && params.screenshot_timing_type) {
        const validTimingTypes = ["load", "networkidle0", "networkidle2"];
        if (!validTimingTypes.includes(params.screenshot_timing_type)) {
            download_data =  {status:"error",error_msg: "screenshot_timing_type timing type must be load, networkidle0 or networkidle2"};
            write_output_to_console(download_data)
            process.exit(0);
        }
    } else {
        params.screenshot_timing_type = "load";
    }

    if ("screenshot_timing" in params) {
        if (typeof params.screenshot_timing !== "number") {
            download_data =  {status:"error",error_msg: "screenshot_timing timing must be numeric"};
            write_output_to_console(download_data)
            process.exit(0);
        }
    } else {
        params.screenshot_timing = 0;
    }


    return params;
}
async function add_metrics_to_visited_page_item(page){
    const domContentLoadedTime =   await page.evaluate(() =>
        window.performance.timing.domContentLoadedEventEnd - window.performance.timing.navigationStart
    );

    const loadTime =   await page.evaluate(() =>
        window.performance.timing.loadEventEnd - window.performance.timing.navigationStart
    );
    visited_page_item.current_url = page.url();
    visited_page_item.image = image;
    visited_page_item.load_time = loadTime;
    visited_page_item.dom_content_loaded_time = domContentLoadedTime;
    visited_page_item.total_data_size = total_data_size;
}
async function handle_request(request) {
    if (request.isInterceptResolutionHandled()) return;
    request.continue();
}


async function handle_response(response) {
    const url = response.url();
    const method = response.request().method();
    const status = response.status();
    let size = 0;
    let error_msg ;

    let start_time = Date.now();
    try {
        const buffer = await response.buffer();
        size = buffer.byteLength
    } catch (error) {
        size = 0;
        error_msg = error.toString();
    }
    total_data_size += size
    const duration = Date.now() - start_time;
    visited_page_item.waterfall_analysis.push({
        url: url,
        method: method,
        status_code: status,
        size: size,
        start_transfer_time: start_time.toString(),
        time: duration.toString(),
        error_msg: error_msg,
    });
}


async function handle_page_changed_data_on_error (page,error){
    download_data.status = "page_changed"
    download_data.error_msg = error.toString()
    visited_page_item.status = "page_changed"
    if(page){
        visited_page_item.current_url = page.url();
        visited_page_item.image  = await page.screenshot({ encoding: 'base64', fullPage: true  })
    }
    visited_page_item.total_data_size = total_data_size;
    download_data.visited_pages.push(visited_page_item);

    write_output_to_console(download_data);
}


async function handle_partial_data_on_error (page,error){
    download_data.status = "partial"
    download_data.error_msg = error.toString()
    visited_page_item.status = "partial"
    if(page) {
        visited_page_item.current_url = page.url();
    }
    visited_page_item.total_data_size = total_data_size;
    download_data.visited_pages.push(visited_page_item);
    write_output_to_console(download_data);
}


async function main() {

    const args = process.argv.slice(2); // Skip the first two arguments


     /* This part is used when input file path is provided. This file contains input data
    if (args.length !== 1) {
        download_data =  {status:"error",error_msg: "Error input_file_path argument is expected"};
        write_output_to_console(download_data)
        return;
    }

       let params = {}
    try {
        const data = fs.readFileSync(args[0], 'utf8');
        params = validateParams(JSON.parse(data));

    } catch (error) {
        const download_data = {status: "error", error_msg: error.toString() };
        write_output_to_console(download_data);
        return
    }
      */

     if (args.length !== 1) {
        download_data =  {status:"error",error_msg: "Error input json data are expected"};
        write_output_to_console(download_data)
        return;
    }

    let params = {}
    try {
        params = validateParams(JSON.parse(args[0]));

    } catch (error) {
        const download_data = {status: "error", error_msg: error.toString() };
        write_output_to_console(download_data);
        return
    }

    const browser = await puppeteer.launch({
        args: [ "--disable-setuid-sandbox",
        "--no-sandbox",
        "--single-process",
        "--no-zygote",
        "--disable-gpu",
        "--disable-dev-shm-usage",],
        executablePath:"/usr/bin/google-chrome-stable"
    });
    const page = await browser.newPage();
    await page.setRequestInterception(true);
    page.on("request",handle_request);
    page.on("response", handle_response)

    let timeoutId;
    if (params.replay_script){
        let timeout = params.element_search_timeout; // don't delete it is used in generated script it is timeout for interacting with a specific locator 0 means no timeout
        page.setDefaultTimeout(0);
        page.setDefaultNavigationTimeout(30000)
        generate_script(params.replay_script,async (error,new_file)=>{
            if(error){
                download_data =  {status:"error",error_msg: error.toString()};
                write_output_to_console(download_data)
                await browser.close()
                return;
            }
            try {
                await Promise.race([
                   (async () => await eval(new_file))(),
                    new Promise((_, reject) => {
                    timeoutId = setTimeout(() => {
                            reject(new Error(`Timeout of ${params.timeout} ms exceeded`));
                        }, params.timeout);
                    }),
                ]);
            } catch (error) {
                 if (error instanceof TimeoutError && error.message.startsWith("Timed out after waiting")) {
                        await handle_page_changed_data_on_error(page,error)
                  }else{
                        await handle_partial_data_on_error(page,error)
                 }
                await browser.close();
                return;
            } finally {
                clearTimeout(timeoutId);
            }

            download_data.status = "completed";
            await browser.close();
            write_output_to_console(download_data)
        });

    }
    else {
        try {
           await Promise.race([
                 (async () => {
                     await page.goto(params.target_host , {waitUntil: params.screenshot_timing_type, timeout: 0})
                     await new Promise(resolve => setTimeout(resolve, params.screenshot_timing))
                     image = await page.screenshot({ encoding: 'base64', fullPage: true  })
                 })(),

                new Promise((_, reject) => {
                    timeoutId = setTimeout(async () => {
                            reject(new Error(`Timeout of ${params.timeout} ms exceeded`));
                        }, params.timeout);
                    }),
                ]);
       } catch (error) {
           await handle_partial_data_on_error(page,error)
           await browser.close();
           return ;
       }
       finally {
            clearTimeout(timeoutId)
        }

        download_data.status = "completed";
        visited_page_item.status = "completed"
        await add_metrics_to_visited_page_item(page);
        download_data.visited_pages.push(visited_page_item);
       write_output_to_console(download_data)
       await browser.close();
    }

}

main();
