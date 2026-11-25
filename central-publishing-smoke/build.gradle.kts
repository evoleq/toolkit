plugins {
    kotlin("jvm") version "2.3.20"
}
val toolkitVersion = providers.gradleProperty("toolkitVersion").get()
dependencies {
    implementation("org.evoleq.toolkit:toolkit-actions:" + toolkitVersion)
    implementation("org.evoleq.toolkit:toolkit-api:" + toolkitVersion)
    implementation("org.evoleq.toolkit:toolkit-ktorx:" + toolkitVersion)
    implementation("org.evoleq.toolkit:toolkit-evolution-runtime:" + toolkitVersion)
    implementation("org.evoleq.toolkit:toolkit-context:" + toolkitVersion)
    implementation("org.evoleq.toolkit:toolkit-serialization-ksp:" + toolkitVersion)
}

val allModules by configurations.creating {
    isCanBeConsumed = false
    isCanBeResolved = true
    attributes {
        attribute(org.gradle.api.attributes.Usage.USAGE_ATTRIBUTE, objects.named(org.gradle.api.attributes.Usage.JAVA_RUNTIME))
        attribute(org.jetbrains.kotlin.gradle.plugin.KotlinPlatformType.attribute, org.jetbrains.kotlin.gradle.plugin.KotlinPlatformType.jvm)
    }
}
val manifest = groovy.json.JsonSlurper().parse(file("../compatibility/modules.json")) as Map<*, *>
val publishedModuleNames = (manifest["modules"] as Map<*, *>).entries
    .filter { (_, value) -> (value as Map<*, *>)["publication"] != "none" }
    .map { (name, _) -> name as String }
check(publishedModuleNames.isNotEmpty())
publishedModuleNames.forEach { moduleName ->
    dependencies.add(allModules.name, "org.evoleq.toolkit:$moduleName:$toolkitVersion")
}
tasks.register("verifyAllModules") {
    doLast {
        check(allModules.resolve().isNotEmpty())
    }
}
