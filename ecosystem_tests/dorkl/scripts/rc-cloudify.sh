alias jqids="jq -r '.[].id'"

xplugins () {
    for plugin in `cfy plugins list --json | jqids`;
        do cfy plugins delete $plugin;
        done
}

xexec () {
    for deployment in `cfy deployments list --json | jqids`;
        do cfy uninstall -p ignore_failure=true $deployment
        done
}

xdep () {
    for deployment in `cfy deployments list --json | jqids`;
        do cfy deployments delete $deployment
        done
}

xblue () {
    for blueprint in `cfy blueprints list --json | jqids`;
        do cfy blueprints delete $blueprint
        done
}

getpluginbyname () {
    cfy plugins list --json | jq -c --arg var $1 '.[] | select( .package_name | contains($var))'
}

getpluginids () {
    getpluginbyname $1 | jq -r '.id'
}

xplugin () {
    for plugin in `getpluginids $1`;
        do cfy plugins delete $plugin
        done
}
