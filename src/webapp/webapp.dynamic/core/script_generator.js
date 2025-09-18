const fs = require('fs');

global.appended_code = `
    await new Promise(resolve => setTimeout(resolve, params.timing_between_steps));
    await page.waitForFunction(() => {
    const body = document.querySelector('body');
    return body && body.offsetWidth > 0 && body.offsetHeight > 0;
    });
    image = await page.screenshot({ encoding: 'base64', fullPage: true  });
    await add_metrics_to_visited_page_item(page);
    visited_page_item.status = "completed"
    total_data_size = 0;
    download_data.visited_pages.push(visited_page_item);
    await init_visited_page_item();
`;

function extractOuterBraces(str) {
    let stack = [];
    let start = -1;

    for (let i = 0; i < str.length; i++) {
        if (str[i] === '{') {
            if (stack.length === 0) {
                start = i;
            }
            stack.push('{');
        } else if (str[i] === '}') {
            stack.pop();
            if (stack.length === 0 && start !== -1) {
                return str.substring(start + 1, i);
            }
        }
    }

    return null;
}

function extractAllBetweenCurlyBraces(str) {
    const results = [];
    let stack = [];
    let start = -1;

    for (let i = 0; i < str.length; i++) {
        if (str[i] === '{') {
            if (stack.length === 0) {
                start = i;
            }
            stack.push('{');
        } else if (str[i] === '}') {
            stack.pop();
            if (stack.length === 0 && start !== -1) {
                results.push(str.substring(start + 1, i));
                start = -1;
            }
        }
    }

    return results; // Return an array of matches
}


function generate_script(user_recorded_file,callback) {
    try{
        let decoded_file = Buffer.from(user_recorded_file, 'base64').toString('utf-8');
        const matches  = extractAllBetweenCurlyBraces(extractOuterBraces(decoded_file))
        let new_file = "(async () => {{\n"+matches[0]+"}\n"
        for (let i = 1; i < matches.length; i++) {
            new_file += "{ \n"+matches[i]
            new_file  += appended_code+"\n}"
        }
        new_file += "\n})()"
        return callback(null,new_file);
    }catch (err){
            return callback(err, null);
    }

}

module.exports = generate_script