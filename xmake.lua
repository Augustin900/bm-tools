add_rules("mode.debug", "mode.release")

target("rdg")
  set_kind("binary")
  add_files("rdg/*.cpp")