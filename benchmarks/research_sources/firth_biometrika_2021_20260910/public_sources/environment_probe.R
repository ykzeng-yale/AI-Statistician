cat(paste0('{"runtime_language":"r","runtime_version":"',
           R.version.string, '","package_versions":{"enrichwith":"',
           as.character(utils::packageVersion("enrichwith")), '"}}\n'))
