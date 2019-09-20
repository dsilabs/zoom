window.addEventListener('load', function() {
    var targets = document.getElementsByClassName('markdown-linker'),
        body = document.getElementsByTagName('body')[0];

    function setupTarget(el) {
        var mdLink = '[' + 
            el.getAttribute('data-link-name') + 
        '](' +
            el.getAttribute('data-link') + 
        ')';
        if (el.className.indexOf('link-image')) mdLink = '!' + mdLink;
        var defaultCls = el.className, clsResetLock = 0, 
            defaultTitle = el.getAttribute('title');
        
        el.addEventListener('click', function(event) {
            event.stopPropagation();
            event.preventDefault();

            var host = document.createElement('textarea');
            host.setAttribute('style', 'width: 0.1px; height: 0.1px; position: absolute; top: 0px; left: 0px;');
            host.textContent = mdLink;

            body.appendChild(host);
            
            host.select();
            host.setSelectionRange(0, 999999);
            document.execCommand('copy');
            body.removeChild(host);

            el.className = el.className.replace(/fa-[a-z-]+/, 'fa-check');
            el.setAttribute('title', 'Copied');
            clsResetLock++;
            setTimeout(function() {
                if (clsResetLock > 1) {
                    clsResetLock--;
                    return;
                }

                el.className = defaultCls;
                el.setAttribute('title', defaultTitle);
                clsResetLock = 0;
            }, 2000);
        });
    }

    for (var i = 0; i < targets.length; i++) {
        setupTarget(targets[i]);
    }
});
