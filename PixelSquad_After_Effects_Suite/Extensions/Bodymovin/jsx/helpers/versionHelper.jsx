/**
 * ====================================================================
 * PixelSquad Creative Suite
 * Copyright (C) 2026 PixelSquad. All Rights Reserved.
 * Author: Mohammed Shahid <hello@pixelsquad.in>
 * Proprietary & Confidential. Unauthorized copying, distribution,
 * modification, or reverse engineering is strictly prohibited.
 * ====================================================================
 */

/*jslint vars: true, plusplus: true, devel: true, nomen: true, regexp: true, indent: 4, maxerr: 50 */
/*global Folder, File, $ */
$.__bodymovin.bm_versionHelper = (function () {
    var ob = {};
    var _version;
    var version_number = '5.12.2';

    function setVersion(data) {
        _version = data;
    }

    function getVersion() {
        return version_number;
    }

    ob.set = setVersion
    ob.get = getVersion

    return ob;
}());