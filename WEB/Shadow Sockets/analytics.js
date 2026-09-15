
/**
 * Shadow Analytics Core v2.1.4
 * (c) 2024 Shadow Analytics Inc.
 * Protocol: MTRK
 */
(function(window, undefined) {
    'use strict';
    var config = {
        ws: 'd3M6Ly9sb2NhbGhvc3Q6NTAwMC9zdHJlYW0vbWV0cmljcw==',
        magic: 'TUFHSUNfSEVBREVSOjB4NEQ1NDUyNEI=',
        protocol: 'UHJvdG9jb2xWZXJzaW9uOjF8WE9SX0tFWToweDcz',
        checksum: btoa('XOR_KEY_DECIMAL:115')
    };
    function decode(str) { try { return atob(str); } catch(e) { return str; } }
    function init() {
        var endpoint = decode(config.ws);
        console.log('[Analytics] Initializing telemetry stream...');
        if (window.location.search.includes('debug=1')) {
            console.log('[DEBUG] Config loaded');
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    window.__analytics = {
        version: '2.1.4',
        debug: function() {
            console.log('WebSocket:', decode(config.ws));
            console.log('Magic Header:', decode(config.magic));
        }
    };
})(window);
